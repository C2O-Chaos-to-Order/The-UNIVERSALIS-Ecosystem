# Website Construction and Agent-Ready Publishing Architecture — UNIVERSALIS

**Boundary:** Public, open and independently inspectable UNIVERSALIS / MotherThread.  
**Owner:** The UNIVERSALIS Ecosystem.  
**Source inventory:** Thirteenth owner-supplied toolchain inventory — Websites.  
**Status:** Open architecture and portable contract proposal implemented on this branch; third-party tools remain candidates; no production site builder or CMS is claimed integrated.

## 1. Architecture purpose

UNIVERSALIS treats a website as a structured, versioned and agent-navigable artifact rather than only rendered HTML. The public toolchain should let developers and agents inspect site structure, propose reviewable changes, validate content and accessibility, and exchange portable site and capability records. Human approval, stale-revision rejection and explicit publish boundaries remain essential even for open implementations.

This repository publishes public architecture, contracts, test fixtures and reference adapters. It must not publish C2O-private website content, credentials, CMS tokens, domains under private operation, deployment secrets, authority decisions, unpublished source, private audit reports or signing keys.

## 2. Open and inspectable website tool candidates

### Agentic site construction and visual collaboration

- **EmDash / EmDash Build:** Cloudflare documents EmDash 1.0 as an Astro-based open-source CMS. EmDash Build is a separate open-source alpha site builder; the documented flow has an agent design a content model, create content through the EmDash MCP server and author Astro pages inside a per-project Cloudflare Sandbox. Git-tracked artifacts, preview/repair and Workers for Platforms publishing are described. Its Cloudflare account and services are architectural dependencies; do not present the Build alpha as fully vendor-independent or self-hosted. Pin release and export/hosting options before adoption.
- **Weave:** owner-supplied collaborative editor proposal: human canvas editing plus agent access to structured state; revision-pinned atomic ChangeSets; stale proposal rejection; human approval before publish; capability manifest/runtime. Exact canonical product source and release remain unresolved. Treat these as useful acceptance requirements until independently identified.
- **OpenPage:** [buildingopen/openpage](https://github.com/buildingopen/openpage), MIT-licensed, self-hosted JSON-first site builder candidate with typed SiteConfig blocks/theme and standalone HTML export. Its JSON model is a reference for structured, diffable site definitions; its AI generation route currently requires provider configuration. It does not itself establish a universal website interchange standard.
- **OSW Studio:** [o-stahl/osw-studio](https://github.com/o-stahl/osw-studio), BYOK browser-based agentic website builder using an IndexedDB-backed virtual filesystem. Browser-local storage is not equivalent to an OS-level security sandbox; inspect the command surface and model-provider data flow.
- **SeldonFrame:** [seldonframe/seldonframe](https://github.com/seldonframe/seldonframe), open-source/self-hostable agent-native website, booking, intake, CRM and agent workspace candidate for agency/local-business front offices.

### Headless CMS and content platforms

- **Strapi MCP:** Strapi's built-in MCP server was introduced in v5.47.0 and reached GA in v5.49.0. Its Admin token controls which operations are exposed, including content creation/update and publishing. Draft/publish lifecycle remains CMS-enforced when permissions are correctly configured. Use least-privilege tokens and require human approval for publish operations.
- **agent-cms:** [jokull/agent-cms](https://github.com/jokull/agent-cms), Cloudflare Workers CMS backed by D1/R2 with GraphQL, FTS5/Vectorize and admin/editor MCP surfaces. Important security default: its README says writes are open when `CMS_WRITE_KEY` is unset. A deploy must fail closed by configuring the write secret or an independently verified auth gateway before exposing write/MCP/publish operations. It has no built-in admin UI, but supplies primitives from which a human editor can be built.
- **AgentCMS:** separate owner-supplied Astro/Cloudflare blog-CMS candidate; exact source identity remains unresolved. Do not conflate with jokull/agent-cms.
- **Webiny:** open-source/self-hosted serverless CMS candidate; the claimed MCP-assisted development and exact integration/release require canonical source and current documentation.
- **Sveltia CMS:** [sveltia/sveltia-cms](https://github.com/sveltia/sveltia-cms), MIT-licensed Git-based headless CMS, with GitHub, GitLab and Gitea/Forgejo backends documented. Its official docs identify working-with-AI/Agent Skill and `llms.txt` materials. Agent integration still must respect backend permissions and repository branch protection.

### Static site generators and publication

- **seite:** Rust-based single-binary static generator. Its docs describe HTML, Markdown, `llms.txt` and `llms-full.txt` outputs and a structured `seite audit` command. Candidate for local-first, agent-operated site generation and deterministic pre-publish checking.
- **vagejs:** static-site generator with JSON command outputs, an MCP server offering read-only site/info/check/page/link tools, and owner-controlled publishing/link approval. This read-only MCP boundary is a useful reference design.
- **staticforge:** owner-supplied CLI/MCP/JSON-schema static site generator candidate; exact upstream and license remain unresolved.
- **ShipStatic:** [shipstatic/mcp](https://github.com/shipstatic/mcp), MIT-licensed hosted/local MCP deployment tool. Its hosted unauthenticated flow provides a URL and claim link; sites without a claim expire after the documented temporary period (currently three days). It is suitable for experiments and disposable prototypes, not private production hosting or a sovereign deployment dependency.

### Web application frameworks and agent-facing interfaces

- **Mastra:** open TypeScript agent/application framework with MCP client/server, workflow and human-in-the-loop patterns. Its docs describe pausing a tool call before execution for human approval. Pin version and review its auth and server exposure model.
- **Cortex:** name collision. The located Cortex project is an API/SDK documentation and MCP generator, not evidence of the supplied AI-first Next.js CRUD framework. The stated framework identity remains unresolved.
- **Bao** and **AgenticAPI:** owner-supplied AI-native runtime/framework candidates; canonical source, supported versions, license, threat model and actual approval enforcement remain unresolved.

### Website auditing, security and accessibility

- **squirrelscan:** [squirrelscan/squirrelscan](https://github.com/squirrelscan/squirrelscan), MIT-licensed CLI, local audit engine and rule packages for coding-agent/CI use. Its current materials describe 300+ rules across 22 categories and CLI/local MCP/agent/CI entry points. The hosted API, cloud worker, dashboard, hosted MCP and some cloud/browser/AI features are separate private services. Telemetry is enabled by default but can be disabled; local offline mode is available. A score is a ruleset-specific diagnostic, not certification.
- **AcuityScan:** website scanner with REST API and native MCP server; public product material advertises 350+ protocol/browser-based checks across security, DNS/email, accessibility, performance, SEO and privacy. The current material describes a hosted scanning service, so classify as hosted/service-dependent until private deployment is demonstrated. Do not send private site targets/results without data-processing review.
- **SyteCheck:** website audit service describing ten scored categories including accessibility, performance, SEO, security headers, broken links, visual/responsive checks and AI visibility. Its product page describes axe-core and WCAG 2.2 AA checks; independently verify scan coverage and result reproducibility.
- **SiteProof:** owner-supplied agent-proof/AEO/accessibility scan candidate; canonical source, rule definitions, API and license remain unresolved.
- **Burp Suite DAST MCP:** PortSwigger's DAST MCP interface connects an AI client to DAST scans/issues through the existing DAST web server and account permissions. Current documentation says it is unavailable on self-hosted deployments that only run CI-driven scans without the dashboard. Treat it as a licensed service integration, not an open or generally self-hostable scanner.

### Content, accessibility and discovery interfaces

A website may expose machine-readable page structures, Markdown alternates, JSON-LD, sitemap, `robots.txt`, `llms.txt`, `llms-full.txt`, `ai.txt` or `AGENTS.md`. Record the existence and verification status of these signals without treating them as access control, a license, consent, publication permission or proof that an AI system has indexed the site.

## 3. Portable public website contracts

The shared v1 schema defines six portable record types:
1. **Site definition:** site/revision identity and digests, rendering targets, page routes and block references, theme digest, lifecycle state, discovery signals and provenance.
2. **Agent capability manifest:** MCP, WebMCP, HTTP API and Agent Skills interaction surfaces; site revision; declared capabilities, operation scopes, auth modes, approval requirements and discovery-signal status.
3. **Site ChangeSet:** revision-pinned typed changes, base/current digests, staleness state, approval and commit references.
4. **Site permission profile:** principal/role, opaque token reference, allowed and denied operations, path scopes, expiry and approval requirements.
5. **Website audit receipt:** scanner/ruleset identity/digest, site revision/content digest, audit scope, findings/severity totals, score, timestamps, evidence and optional signature metadata.
6. **Site publish receipt:** preview/publish/deploy/DNS/unpublish/rollback event, target and artifact digest, operator/approval, outcome, audit references, time and optional signature metadata.

The schema uses opaque IDs and digests. It excludes credentials, tokens, deployment secrets, raw private content, private policy bodies and signing-key values. The fixtures are synthetic and use reserved example references.

## 4. Human-agent ChangeSet and WebMCP requirements

The **WebMCP** surface is an emerging browser API, not a substitute for backend MCP or authorization. The Web Machine Learning Community Group's 2026-11-11 report is a draft, not a W3C Standard or a W3C-track standard; Chromium documentation describes early preview. The published draft describes JavaScript tools exposed by a web application to agents.

The portable contract therefore records WebMCP maturity/status and defines our required semantics independently:
- structured, inspectable site/editor state;
- changes proposed as a typed ChangeSet rather than blind DOM manipulation;
- proposals pinned to a site revision/digest;
- any intervening edit makes a stale proposal invalid;
- atomic review/commit semantics where implemented;
- publish/deploy/DNS actions held behind a human/owner gate;
- no route from an agent tool call directly to production publication without independent authorization.

These are proposed UNIVERSALIS acceptance requirements, not guarantees supplied by the draft API itself. Browser support, origin isolation, session and permission model, tool discovery, user gesture requirements and data exposure must be tested per browser/runtime.

## 5. Source and claim discipline

Known source starting points:
- [Cloudflare EmDash 1.0 / EmDash Build alpha](https://blog.cloudflare.com/emdash-cms-plugin-registry) and [EmDash deployment docs](https://developers.cloudflare.com/workers/framework-guides/web-apps/emdash/).
- [Strapi MCP GA announcement](https://strapi.io/blog/the-strapi-mcp-server-is-now-ga).
- [OpenPage](https://github.com/buildingopen/openpage).
- [OSW Studio](https://github.com/o-stahl/osw-studio).
- [SeldonFrame](https://github.com/seldonframe/seldonframe).
- [agent-cms](https://github.com/jokull/agent-cms).
- [Sveltia CMS](https://github.com/sveltia/sveltia-cms).
- [seite documentation](https://seite.sh/docs/getting-started) and [vagejs documentation](https://vagejs.com/faq/).
- [ShipStatic MCP](https://github.com/shipstatic/mcp).
- [squirrelscan](https://github.com/squirrelscan/squirrelscan) and [its FAQ](https://docs.squirrelscan.com/faq).
- [AcuityScan](https://www.acuityscan.com/about) and [SyteCheck](https://sytecheck.app/features).
- [Mastra MCP docs](https://mastra.ai/docs/connections/mcp) and [Mastra human-in-the-loop docs](https://mastra.ai/docs/agents/human-in-the-loop).
- [PortSwigger DAST MCP documentation](https://portswigger.net/burp/documentation/dast/user-guide/using-ai/mcp-server).
- [WebMCP draft report](https://webmachinelearning.github.io/webmcp/) and [Chrome WebMCP documentation](https://developer.chrome.com/docs/ai/webmcp).

Exact upstreams for Weave, AgentCMS, Webiny MCP specifics, staticforge, supplied Cortex identity, Bao, AgenticAPI and SiteProof remain unresolved. The sovereign providers/platforms BrickOS, Burhan Platform, Drumee and Vaulltcore also require exact source, license and deployment-model review. Do not conflate similarly named projects.

All numbers (audit rules, security checks, scores, tool integrations, anti-DDoS capability, privacy/sovereignty assurances and performance claims) are source-reported claims until independently reproduced.

## 6. Implementation status and limits

Implemented on this proposal branch:
- portable website interoperability JSON Schema v1;
- six synthetic positive records;
- semantic validator and eleven negative cases;
- public GitHub Actions workflow for contract validation.

Not implemented or claimed:
- no UNIVERSALIS website, CMS, hosting platform or production builder deployed by this change;
- no third-party builder, CMS, framework, auditor or MCP integration installed;
- no WebMCP integration enabled or browser capability assumed;
- no live website crawled or scanned;
- no content published or deployment performed;
- no production signature service used;
- no accessibility or security certification asserted.

CI validates schema and semantic fixture behavior only. It does not prove source-product suitability, website quality, WCAG conformance, privacy, security, protocol interoperability, performance or production deployment.
