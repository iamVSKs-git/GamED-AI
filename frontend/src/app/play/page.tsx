'use client';

import { useState, useCallback, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import ModeToggle from '@/components/templates/AlgorithmGame/components/ModeToggle';

const InteractiveDiagramGame = dynamic(
  () => import('@/components/templates/InteractiveDiagramGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

const StateTracerGame = dynamic(
  () => import('@/components/templates/AlgorithmGame/StateTracerGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

const BugHunterGame = dynamic(
  () => import('@/components/templates/AlgorithmGame/BugHunterGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

const AlgorithmBuilderGame = dynamic(
  () => import('@/components/templates/AlgorithmGame/AlgorithmBuilderGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

const ComplexityAnalyzerGame = dynamic(
  () => import('@/components/templates/AlgorithmGame/ComplexityAnalyzerGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

const ConstraintPuzzleGame = dynamic(
  () => import('@/components/templates/AlgorithmGame/ConstraintPuzzleGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

const AlgorithmMultiSceneGame = dynamic(
  () => import('@/components/templates/AlgorithmGame/AlgorithmMultiSceneGame'),
  { ssr: false, loading: () => <GameSkeleton /> }
);

function GameSkeleton() {
  return (
    <div className="animate-pulse space-y-4 p-8">
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
      <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded" />
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function GameRenderer({ blueprint, gameType, mode, onComplete }: { blueprint: any; gameType: string; mode: 'learn' | 'test'; onComplete: (score: number) => void }) {
  if (gameType === 'interactive_diagram') {
    return <InteractiveDiagramGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
  }

  if (gameType === 'algorithm') {
    const isMultiScene = blueprint?.scenes && Array.isArray(blueprint.scenes) && blueprint.scenes.length > 1;
    if (isMultiScene) {
      return <AlgorithmMultiSceneGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
    }

    const subtype = blueprint?.templateSubType || blueprint?.gameSubType || '';
    switch (subtype) {
      case 'state_tracer':
        return <StateTracerGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
      case 'bug_hunter':
        return <BugHunterGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
      case 'algorithm_builder':
        return <AlgorithmBuilderGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
      case 'complexity_analyzer':
        return <ComplexityAnalyzerGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
      case 'constraint_puzzle':
        return <ConstraintPuzzleGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
      default:
        return <StateTracerGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
    }
  }

  return <InteractiveDiagramGame blueprint={blueprint} onComplete={onComplete} gameplayMode={mode} />;
}

function PlayPageContent() {
  const searchParams = useSearchParams();
  const gameId = searchParams.get('game');

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [gameData, setGameData] = useState<any>(null);
  const [mode, setMode] = useState<'learn' | 'test'>('learn');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!gameId) return;
    setLoading(true);
    setError(null);
    fetch(`/games/${gameId}.json`)
      .then(res => {
        if (!res.ok) throw new Error(`Game "${gameId}" not found`);
        return res.json();
      })
      .then(data => { setGameData(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [gameId]);

  const handleFile = useCallback((file: File) => {
    setError(null);
    setLoading(true);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string);
        setGameData(data);
        setLoading(false);
      } catch {
        setError('Invalid JSON file');
        setLoading(false);
      }
    };
    reader.readAsText(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.json')) {
      handleFile(file);
    } else {
      setError('Please drop a .json file');
    }
  }, [handleFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handlePaste = useCallback(() => {
    navigator.clipboard.readText().then(text => {
      try {
        const data = JSON.parse(text);
        setGameData(data);
        setError(null);
      } catch {
        setError('Clipboard does not contain valid JSON');
      }
    }).catch(() => {
      setError('Could not read clipboard');
    });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading game...</p>
        </div>
      </div>
    );
  }

  if (!gameData) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-lg w-full">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">GamED-AI Player</h1>
            <ThemeToggle />
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-12 text-center transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
            }`}
          >
            <div className="text-4xl mb-4">🎮</div>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
              Load a Game Blueprint
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Drop a JSON file here, or use the options below
            </p>

            <div className="flex flex-col gap-3">
              <label className="cursor-pointer px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors inline-block">
                Choose File
                <input type="file" accept=".json" onChange={handleFileInput} className="hidden" />
              </label>

              <button
                onClick={handlePaste}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Paste from Clipboard
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <p className="mt-6 text-xs text-gray-400 dark:text-gray-500 text-center">
            Generate blueprints with: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">python run.py &quot;Your question&quot;</code>
          </p>
        </div>
      </div>
    );
  }

  const blueprint = gameData.blueprint || gameData;
  const gameType = gameData.gameType || blueprint.templateType || 'interactive_diagram';
  const title = gameData.title || blueprint.title || 'Game';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setGameData(null)}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            >
              &larr; Load another
            </button>
            <span className="text-gray-300 dark:text-gray-600">|</span>
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
              {title}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <ModeToggle mode={mode} onToggle={setMode} />
            <ThemeToggle />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <GameRenderer
          blueprint={blueprint}
          gameType={gameType}
          mode={mode}
          onComplete={(score) => console.log('Game complete, score:', score)}
        />
      </div>
    </div>
  );
}

export default function PlayPage() {
  return (
    <Suspense fallback={<GameSkeleton />}>
      <PlayPageContent />
    </Suspense>
  );
}
