"use client";

import React, { useEffect, useState, useCallback } from "react";
import SpotlightCard from "@/components/ui/SpotlightCard";
import KineticHeader from "@/components/ui/KineticHeader";
import CyberGridBackground from "@/components/ui/CyberGridBackground";

// ── Provider catalogue ────────────────────────────────────────────────────────
const PROVIDERS = [
  {
    id: "gemini",
    label: "Google Gemini",
    model: "gemini-2.5-flash",
    note: "Platform hosted · default fallback",
    isHosted: true,
  },
  {
    id: "openai",
    label: "OpenAI",
    model: "gpt-4o-mini",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "anthropic",
    label: "Anthropic Claude",
    model: "claude-sonnet-4-5",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "mistral",
    label: "Mistral AI",
    model: "mistral-small-latest",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "groq",
    label: "Groq",
    model: "llama-3.3-70b-versatile",
    note: "BYOK — ultra-fast inference",
    isHosted: false,
  },
  {
    id: "cohere",
    label: "Cohere",
    model: "command-r-plus-08-2024",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "xai",
    label: "xAI Grok",
    model: "grok-3-mini",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "deepseek",
    label: "DeepSeek",
    model: "deepseek-chat",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "together",
    label: "Together AI",
    model: "Llama-3.3-70B-Instruct-Turbo",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
  {
    id: "nemotron",
    label: "Nvidia Nemotron",
    model: "llama-3.1-nemotron-70b-instruct",
    note: "BYOK — your key, your quota",
    isHosted: false,
  },
];

// ── Types ─────────────────────────────────────────────────────────────────────
interface ApiKeyStatus {
  provider: string;
  connected: boolean;
  created_at?: string;
  last_used_at?: string;
}

// ── API helpers ──────────────────────────────────────────────────────────────
function getApiBase(): string {
  if (typeof window === "undefined") return "";
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    (window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1"
      ? "https://telex-api.onrender.com"
      : "http://localhost:8000")
  );
}

async function fetchKeys(): Promise<ApiKeyStatus[]> {
  const res = await fetch(`${getApiBase()}/api/settings/api-keys`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(`Failed to load API keys (${res.status} ${res.statusText})`);
  }
  const data = await res.json();
  return data.keys ?? [];
}

async function saveKey(provider: string, key: string): Promise<boolean> {
  const res = await fetch(`${getApiBase()}/api/settings/api-keys`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, key }),
  });
  return res.ok;
}

async function removeKey(provider: string): Promise<boolean> {
  const res = await fetch(
    `${getApiBase()}/api/settings/api-keys/${provider}`,
    { method: "DELETE", credentials: "include" }
  );
  return res.ok;
}

// ── Provider card ────────────────────────────────────────────────────────────
function ProviderCard({
  provider,
  status,
  onSave,
  onRemove,
}: {
  provider: (typeof PROVIDERS)[0];
  status?: ApiKeyStatus;
  onSave: (id: string, key: string) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
}) {
  const [inputKey, setInputKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showInput, setShowInput] = useState(false);

  const isConnected = Boolean(status?.connected);

  const handleSave = async () => {
    if (!inputKey.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await onSave(provider.id, inputKey.trim());
      setInputKey("");
      setShowInput(false);
    } catch {
      setError("Failed to save key. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    setRemoving(true);
    setError(null);
    try {
      await onRemove(provider.id);
    } catch {
      setError("Failed to remove key.");
    } finally {
      setRemoving(false);
    }
  };

  return (
    <SpotlightCard
      className={`p-4 transition-all duration-300 ${
        isConnected ? "border-emerald-500/40" : ""
      }`}
      enableTilt={!provider.isHosted}
    >
      <div className="flex flex-col gap-3">
        {/* Header row */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-white font-medium">
                {provider.label}
              </span>
              {isConnected ? (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 tracking-widest">
                  ● CONNECTED
                </span>
              ) : provider.isHosted ? (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-white/10 text-white border border-white/20 tracking-widest">
                  HOSTED
                </span>
              ) : (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-white/10 text-[#71717A] tracking-widest">
                  NOT CONNECTED
                </span>
              )}
            </div>
            <div className="font-mono text-[11px] text-[#71717A]">
              {provider.note} · <span className="text-[#52525B]">{provider.model}</span>
            </div>
            {status?.last_used_at && (
              <div className="font-mono text-[10px] text-[#52525B]">
                Last used: {new Date(status.last_used_at).toLocaleDateString()}
              </div>
            )}
          </div>

          {/* Actions */}
          {!provider.isHosted && (
            <div className="flex items-center gap-2 shrink-0">
              {isConnected ? (
                <>
                  <button
                    id={`btn-rekey-${provider.id}`}
                    onClick={() => setShowInput((v) => !v)}
                    className="font-mono text-[11px] px-3 py-1.5 rounded border border-white/20 text-[#A1A1AA] hover:text-white hover:border-white/40 transition-colors"
                  >
                    Rotate
                  </button>
                  <button
                    id={`btn-remove-${provider.id}`}
                    onClick={handleRemove}
                    disabled={removing}
                    className="font-mono text-[11px] px-3 py-1.5 rounded border border-red-500/30 text-red-400 hover:border-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                  >
                    {removing ? "Removing…" : "Remove"}
                  </button>
                </>
              ) : (
                <button
                  id={`btn-connect-${provider.id}`}
                  onClick={() => setShowInput((v) => !v)}
                  className="font-mono text-[11px] px-3 py-1.5 rounded bg-white text-black font-semibold hover:bg-white/90 transition-colors"
                >
                  Connect
                </button>
              )}
            </div>
          )}
        </div>

        {/* Key input (inline, masked) */}
        {showInput && !provider.isHosted && (
          <div className="flex gap-2 pt-1">
            <input
              id={`input-key-${provider.id}`}
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              placeholder="Paste your API key…"
              autoComplete="off"
              autoFocus
              className="flex-1 font-mono text-xs bg-white/5 border border-white/20 rounded px-3 py-2 text-white placeholder-[#52525B] focus:outline-none focus:border-white/40 transition-colors"
            />
            <button
              id={`btn-save-${provider.id}`}
              onClick={handleSave}
              disabled={saving || !inputKey.trim()}
              className="font-mono text-[11px] px-4 py-2 rounded bg-white text-black font-semibold hover:bg-white/90 transition-colors disabled:opacity-40"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}

        {error && (
          <p className="font-mono text-[11px] text-red-400">{error}</p>
        )}
      </div>
    </SpotlightCard>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const [keyStatuses, setKeyStatuses] = useState<ApiKeyStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadKeys = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const keys = await fetchKeys();
      setKeyStatuses(keys);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load keys";
      setLoadError(message);
      // Preserves existing keyStatuses rather than marking every provider as disconnected
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const handleSave = async (providerId: string, key: string) => {
    const ok = await saveKey(providerId, key);
    if (!ok) throw new Error("save failed");
    await loadKeys();
  };

  const handleRemove = async (providerId: string) => {
    const ok = await removeKey(providerId);
    if (!ok) throw new Error("remove failed");
    await loadKeys();
  };

  const statusMap = new Map(keyStatuses.map((k) => [k.provider, k]));

  return (
    <div className="flex flex-col gap-10 relative z-10">
      <CyberGridBackground />

      <KineticHeader
        badge="CONFIGURATION"
        title="Settings & Integrations"
        subtitle="Bring your own API keys for any supported LLM provider. Keys are encrypted at rest — they are never logged or returned after saving."
      />

      {/* BYOK key management */}
      <section className="flex flex-col gap-4">
        <div>
          <h2 className="font-mono font-semibold text-base text-white tracking-tight">
            LLM Provider Keys
          </h2>
          <p className="font-sans text-sm text-[#A1A1AA] mt-1">
            Telex uses your stored key when generating patches. Without a key, the
            platform&#39;s hosted Gemini is used as fallback — zero config required.
          </p>
        </div>

        {loadError && (
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 font-mono text-xs">
            <span>{loadError}</span>
            <button
              id="btn-retry-load-keys"
              onClick={loadKeys}
              className="px-3 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-200 transition-colors cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col gap-3">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="h-16 rounded-xl bg-white/5 border border-white/10 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {PROVIDERS.map((p) => (
              <ProviderCard
                key={p.id}
                provider={p}
                status={statusMap.get(p.id)}
                onSave={handleSave}
                onRemove={handleRemove}
              />
            ))}
          </div>
        )}
      </section>

      {/* GitHub Integration */}
      <section className="flex flex-col gap-4">
        <h2 className="font-mono font-semibold text-base text-white tracking-tight">
          Connected Repositories &amp; GitHub App
        </h2>
        <SpotlightCard className="p-5" enableTilt={false}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex flex-col gap-1">
              <div className="font-mono text-sm text-white font-medium flex items-center gap-2">
                <span>telex-agent-dev</span>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-white/10 text-white border border-white/20">
                  INSTALLED
                </span>
              </div>
              <p className="font-sans text-xs text-[#A1A1AA]">
                Connect any personal or organization repository to grant autonomous PR self-healing permissions.
              </p>
            </div>
            <a
              id="btn-connect-repo"
              href={`https://github.com/apps/${process.env.NEXT_PUBLIC_GITHUB_APP_NAME || "telex-agent-dev"}/installations/new`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-white text-black font-mono font-semibold text-xs transition-all hover:bg-white/90 hover:shadow-[0_0_15px_rgba(255,255,255,0.2)] active:scale-[0.98] shrink-0"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>Connect New Repo</span>
            </a>
          </div>
        </SpotlightCard>
      </section>

      {/* Notifications */}
      <section className="flex flex-col gap-4">
        <h2 className="font-mono font-semibold text-base text-white tracking-tight">
          Webhook Notifications
        </h2>
        <div className="flex flex-col gap-3">
          {[
            { label: "PR opened", detail: "When Telex opens a new patch PR after verification" },
            { label: "PR merged", detail: "When a self-healed patch PR is merged" },
            { label: "Scan complete", detail: "After each automated repository AST scan" },
          ].map((n) => (
            <SpotlightCard key={n.label} className="p-4" enableTilt={false}>
              <label className="flex items-center justify-between cursor-pointer w-full">
                <div>
                  <div className="font-mono text-sm text-white">{n.label}</div>
                  <div className="font-mono text-[11px] text-[#71717A]">{n.detail}</div>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  className="accent-white w-4 h-4 cursor-pointer"
                />
              </label>
            </SpotlightCard>
          ))}
        </div>
      </section>
    </div>
  );
}
