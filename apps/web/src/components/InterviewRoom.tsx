import { useEffect, useState } from 'react';
import { LiveKitRoom, RoomAudioRenderer, StartAudio, useConnectionState, useLocalParticipant, useRoomContext } from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';

type InterviewRoomProps = {
  token: string;
  serverUrl: string;
  sessionId: string;
  company: string;
  role: string;
  roundName: string;
  onEnd: (durationSeconds: number) => Promise<void>;
};

export default function InterviewRoom(props: InterviewRoomProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const startedAt = Date.now();
    const interval = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => window.clearInterval(interval);
  }, []);

  async function handleEnd() {
    setEnding(true);
    setError('');
    try {
      await props.onEnd(elapsedSeconds);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not finish this interview. Please try again.');
      setEnding(false);
    }
  }

  const minutes = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0');
  const seconds = (elapsedSeconds % 60).toString().padStart(2, '0');

  return (
    <main className="interview-room-page">
      <header className="interview-room-header">
        <a className="brand" href="/"><span className="brand-mark">i.</span> interview shala</a>
        <span className="interview-session-id">SESSION · {props.sessionId.slice(0, 8).toUpperCase()}</span>
      </header>
      <section className="interview-room-content">
        <p className="eyebrow">LIVE INTERVIEW</p>
        <h1>{props.roundName}</h1>
        <p className="interview-room-subtitle">{props.role} at {props.company}</p>
        <div className="interview-orb" aria-hidden="true"><span /></div>
        <LiveKitRoom
          token={props.token}
          serverUrl={props.serverUrl}
          connect
          audio
          video={false}
          onError={(cause) => setError(cause.message || 'The voice connection encountered an error.')}
        >
          <RoomAudioRenderer />
          <StartAudio label="Enable interviewer audio" />
          <RoomControls
            elapsedTime={minutes + ':' + seconds}
            ending={ending}
            onEnd={handleEnd}
          />
        </LiveKitRoom>
        <p className="interview-room-caption">Speak naturally. The interviewer will ask one question at a time.</p>
        <p className="interview-room-trust">Your voice session is connected directly to the interview room. Transcript turns are saved by the server worker.</p>
        {error && <p className="error-message interview-room-error" role="alert">{error}</p>}
      </section>
    </main>
  );
}

function RoomControls({
  elapsedTime,
  ending,
  onEnd,
}: {
  elapsedTime: string;
  ending: boolean;
  onEnd: () => Promise<void>;
}) {
  const room = useRoomContext();
  const connectionState = useConnectionState();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const [micError, setMicError] = useState('');

  async function endInterview() {
    try {
      await room.disconnect();
      await onEnd();
    } catch (cause) {
      setMicError(cause instanceof Error ? cause.message : 'Could not disconnect cleanly. Please try again.');
    }
  }

  async function toggleMicrophone() {
    setMicError('');
    try {
      await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
    } catch {
      setMicError('Microphone access failed. Check your browser permissions and try again.');
    }
  }

  const connected = connectionState === ConnectionState.Connected;
  const connectionLabel = connected
    ? 'Connected'
    : connectionState === ConnectionState.Connecting
      ? 'Connecting to interviewer…'
      : connectionState === ConnectionState.Reconnecting
        ? 'Reconnecting…'
        : connectionState === ConnectionState.Disconnected
      ? 'Disconnected'
      : 'Waiting for connection';

  return (
    <div className="interview-controls">
      <div className="interview-status"><span className={connected ? 'status-dot status-dot--live' : 'status-dot'} />{connectionLabel}</div>
      <div className="interview-timer" aria-live="off">{elapsedTime}</div>
      <div className="interview-control-actions">
        <button className={isMicrophoneEnabled ? 'mic-button' : 'mic-button mic-button--muted'} type="button" onClick={() => void toggleMicrophone()} disabled={!connected} aria-pressed={isMicrophoneEnabled}>
          {isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
        </button>
        <button className="end-interview-button" type="button" onClick={() => void endInterview()} disabled={ending || !connected}>
          {ending ? 'Ending…' : 'End interview'}
        </button>
      </div>
      {micError && <p className="error-message" role="alert">{micError}</p>}
    </div>
  );
}
