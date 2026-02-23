# Plugin System (Stage 2 Only)

## Scope Note

The plugin system is **not part of Stage 1 MVP**.

Stage 1 uses one built-in in-process source adapter: OpenAlex.

Plugin work starts in Stage 2 Wave 4 only after core workflow validation.

## Why Deferred

1. Plugins add operational/security surface before core value is proven.
2. Stage 1 priority is fast validation of subscribe -> score -> act.
3. Extensibility is useful only after workflow fit is established.

## Stage 2 Plugin Types

1. Source plugins (ingestion)
2. Processor plugins (custom scoring/enrichment)
3. Action plugins (external actions from pipeline events)

## Registration Model

```typescript
interface PluginRegistration {
  id: string;
  workspaceId: string;
  name: string;
  type: 'source' | 'processor' | 'action';
  url: string;
  auth: {
    type: 'none' | 'bearer' | 'basic' | 'hmac';
    credentials?: string; // encrypted
  };
  configSchema?: unknown;
  createdAt: Date;
}
```

## Security Baseline (Stage 2)

1. HMAC request signing
2. Strict SSRF protection (block private/reserved ranges)
3. Timeouts and bounded retries
4. Per-plugin rate limits
5. Zod validation on all request/response boundaries

## Rollout Gates

Plugins remain disabled until all of the following are true:

1. Stage 1 acceptance tests remain green under load
2. Stage 2 tenancy and RLS foundations are complete
3. Audit logging exists for plugin invocations
4. Failure isolation is validated (plugin failures never block core loop)
