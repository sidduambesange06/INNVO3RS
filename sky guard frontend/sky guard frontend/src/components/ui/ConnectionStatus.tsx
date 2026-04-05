import { useSystemStore } from '../../store/systemStore';

export default function ConnectionStatus() {
  const isConnected = useSystemStore((state) => state.isConnected);

  if (isConnected) {
    return (
      <div className="flex items-center gap-2 text-xs text-green-400">
        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
        <span className="font-mono">LIVE</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs text-red-400">
      <div className="w-2 h-2 rounded-full bg-red-400"></div>
      <span className="font-mono">DISCONNECTED</span>
    </div>
  );
}
