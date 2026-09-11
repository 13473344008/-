# Product Digital Identity — static public site

T11 local implementation; not deployed. Original `../site/` remains the frozen POC.

- `/b/{batch_code}` reads `/published/{batch_code}.json` and compares it with the matching immutable `/versions/{batch_code}/vN.json` before rendering.
- `/b/{batch_code}/v/{version}` reads only that historical snapshot.
- `?lang=en|zh-CN|es|ar|fr|de` selects presentation; default English.
- Images come only from validated `/assets/sha256/xx/<hash>.png` paths.
- Public schema, renderer and URL builder have no framework or network dependencies.
- The admin imports the renderer for authenticated, watermarked previews. It never writes draft files here.

`deploy/nginx.conf.template` is the actual local acceptance configuration template. Replace its `@SITE@`, `@RELEASE@`, `@RUNTIME@`, `@SOURCE@` placeholders for an isolated local environment. It listens only on 127.0.0.1:19540. No proxying, TLS, DNS, Caddy or production configuration is included.

Public base origin is supplied to the admin build using `VUE_APP_PUBLIC_BASE_URL` and `VUE_APP_PUBLIC_MODE=production|local`. Production mode requires a non-local HTTPS origin. Local HTTP requires explicit local mode. No domain is assumed and no QR image is generated.

See `../docs/T11_PUBLIC_SITE_QR_URL.md` for evidence, boundaries and known limitations. All T11 local services are stopped after acceptance tests.

2026-09-11 manual acceptance feedback: customer pages no longer render publication metadata (version, issue time, schema, publication kind or rollback source). Snapshot metadata remains available for validation and backend history; this is a presentation change, not removal from publicly served JSON.
