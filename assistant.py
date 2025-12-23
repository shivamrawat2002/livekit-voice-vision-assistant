import asyncio
from typing import Annotated
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, tokenize, tts
from livekit.agents.llm import (
    ChatContext,
    ChatImage,
    ChatMessage,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero

load_dotenv()


async def get_video_track(room: rtc.Room):
    """Get the first video track from the room. We'll use this track to process images."""

    video_track = asyncio.Future[rtc.RemoteVideoTrack]()

    for _, participant in room.remote_participants.items():
        for _, track_publication in participant.track_publications.items():
            if track_publication.track is not None and isinstance(
                track_publication.track, rtc.RemoteVideoTrack
            ):
                video_track.set_result(track_publication.track)
                print(f"Using video track {track_publication.track.sid}")
                break

    return await video_track


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    print(f"Room name: {ctx.room.name}")

    chat_context = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content=(
                    "Your name is Alloy. You are a funny, witty bot. Your interface with users will be voice and vision. "
                    "Respond with short and concise answers. Avoid using unpronouncable punctuation or emojis."
                ),
            )
        ]
    )

    gpt = openai.LLM(model="gpt-4o")

    # Since OpenAI does not support streaming TTS, we'll use it with a StreamAdapter
    # to make it compatible with the VoiceAssistant
    openai_tts = tts.StreamAdapter(
        tts=openai.TTS(voice="alloy"),
        sentence_tokenizer=tokenize.basic.SentenceTokenizer(),
    )

    latest_image: rtc.VideoFrame | None = None

    # Create AssistantFunction with access to latest_image and other necessary context
    class AssistantFunction(agents.llm.FunctionContext):
        """This class is used to define functions that will be called by the assistant."""

        @agents.llm.ai_callable(
            description=(
                "Called when asked to evaluate something that would require vision capabilities, "
                "for example, an image, video, or the webcam feed."
            )
        )
        async def image(
            self,
            user_msg: Annotated[
                str,
                agents.llm.TypeInfo(
                    description="The user message that triggered this function"
                ),
            ],
        ):
            print(f"Message triggering vision capabilities: {user_msg}")
            
            # Check if we have a video frame available
            if latest_image is None:
                return "No video feed available at the moment. Please ensure your camera is on."
            
            # Return a message indicating we'll process the image
            return "Processing the image from your camera..."

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),  # We'll use Silero's Voice Activity Detector (VAD)
        stt=deepgram.STT(),  # We'll use Deepgram's Speech To Text (STT)
        llm=gpt,
        tts=openai_tts,  # We'll use OpenAI's Text To Speech (TTS)
        fnc_ctx=AssistantFunction(),
        chat_ctx=chat_context,
    )

    async def _answer(text: str, use_image: bool = False):
        """
        Answer the user's message with the given text and optionally the latest
        image captured from the video track.
        """
        content: list[str | ChatImage] = [text]
        if use_image and latest_image:
            print(f"Using image in response for query: {text}")
            content.append(ChatImage(image=latest_image))

        chat_context.messages.append(ChatMessage(role="user", content=content))

        stream = gpt.chat(chat_ctx=chat_context)
        await assistant.say(stream, allow_interruptions=True)

    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle incoming data packets (text messages)."""
        if data.kind == rtc.DataPacketKind.KIND_RELIABLE:
            message = data.data.decode("utf-8")
            print(f"Received text message: {message}")
            asyncio.create_task(_answer(message, use_image=False))

    @assistant.on("function_calls_finished")
    def on_function_calls_finished(called_functions: list[agents.llm.CalledFunction]):
        """This event triggers when an assistant's function call completes."""

        if len(called_functions) == 0:
            return

        user_msg = called_functions[0].call_info.arguments.get("user_msg")
        if user_msg:
            print(f"Function call finished, answering with image for: {user_msg}")
            asyncio.create_task(_answer(user_msg, use_image=True))

    assistant.start(ctx.room)

    await asyncio.sleep(1)
    await assistant.say("Hi there! How can I help?", allow_interruptions=True)

    # Start video processing
    async def process_video():
        """Continuously capture video frames."""
        nonlocal latest_image
        
        while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
            try:
                video_track = await get_video_track(ctx.room)
                async for event in rtc.VideoStream(video_track):
                    # Continually grab the latest image from the video track
                    latest_image = event.frame
            except Exception as e:
                print(f"Error processing video: {e}")
                await asyncio.sleep(1)

    # Run video processing as a background task
    asyncio.create_task(process_video())

    # Keep the connection alive
    while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
        await asyncio.sleep(1)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))   