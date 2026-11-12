# UNIVERSALIS OS Provisioning and Virtualization Architecture

**Owner:** UNIVERSALIS / MotherThread  
**Boundary:** Public, reusable, independently operable. Do not include C2O-private credentials, tenant data, authority state, policies, or operational logs.  
**Status:** Proposed; portable interfaces and candidate verification pending.

## 1. Requirement

UNIVERSALIS OS provisioning must support heterogeneous guest operating systems and devices through open, composable, replaceable tools. It must distinguish full-system emulation, Type-1/Type-2 virtualization, namespace containers, and microVMs; these are not interchangeable security boundaries. A device-independent control API and a non-immersive management path are required.

## 2. Candidate toolchain

| Layer | Owner-supplied candidates | Intended role |
|---|---|---|
| Open VM bootstrap / emulation | Quickemu; anyvm.py; GNOME Boxes; QEMU | Download/configure guest media, create full VMs, broad OS emulation |
| Full-OS namespace containers | systemd-nspawn; sdme; Docker; Podman | Lightweight Linux system environments; privileged containers treated as high risk |
| MicroVM | cocoon; Cloud Hypervisor; Firecracker | Lightweight VM execution; select backend by supported guest OS and device constraints |
| AI/MCP provisioning | mcp-virtualbox; NervOS; Celesto | Agent-accessible VM setup and disposable computer environments |
| Shared management | libvirt; virt-manager; OpenStack | Optional provider-neutral management and image distribution |
| Immersive interfaces | XARP; Meta Immersive Web SDK (IWSDK); spatial-kg; Constellation; Agent Hands | Open WebXR control and inventory visualization |

Quickemu and QEMU are broad guest provisioning/emulation candidates. systemd-nspawn is a Linux system-container mechanism, not a full hardware VM. Docker/Podman containers using privileged mode are not equivalent to a microVM and must not be treated as a strong isolation boundary. Firecracker and Cloud Hypervisor have distinct guest compatibility; select based on verified support rather than assuming parity. cocoon and mcp-virtualbox remain unverified candidates until their source, releases, security, and behavior are checked.

## 3. Runtime selection rules

- Use a full VM or microVM when guest-kernel isolation or non-Linux guest support is required.
- Use systemd-nspawn for a Linux userspace/systemd environment where namespace-container isolation is sufficient.
- Do not default to privileged Docker/Podman containers for untrusted agent workloads.
- Select Firecracker only for verified compatible Linux/OSv workloads; use Cloud Hypervisor or another VM backend where the required guest is supported.
- Preserve portability through a versioned guest manifest: OS family, release, architecture, firmware, kernel, rootfs/image digest, resource requirements, networking, device access, and boot/test command.
- Provide a headless/API path and a conventional desktop path; XR is optional, never the only management interface.

## 4. Safe provisioning lifecycle

1. Discover the host and declared guest requirements.
2. Resolve official image source, license, architecture, digest, and signature.
3. Generate a reproducible configuration and preview the resource/network/device permissions.
4. Require explicit approval for privileged host access, persistent storage changes, external network exposure, or destructive image replacement.
5. Start the VM/container with bounded resources and least privilege.
6. Verify guest boot, expected OS release, network restrictions, isolation boundary, and health checks.
7. Record the image digest, config hash, runtime/backend version, approvals, logs, and test results.
8. Stop, snapshot, export, or erase according to the declared lifecycle and consent/retention policy.

## 5. Shared bridge and C2O boundary

libvirt/virt-manager and OpenStack are candidate neutral management surfaces. C2O may operate a private deployment while UNIVERSALIS exposes independently deployable adapters and public interface schemas. The bridge must use versioned APIs with tenant separation and explicit authorization. No C2O credential, private image, private network detail, tenant policy, or authority token is copied into this public repository.

## 6. Immersive management

XARP and IWSDK are open interface candidates; spatial-kg and Constellation may represent VM, network, and host relationships in 3D. Agent Hands is a hardware-location/interactivity candidate. Camera, microphone, gaze, hand-tracking, and spatial data require explicit consent and minimization. Every immersive action must have the same approval and audit guarantees as the API/desktop action, and the full task must remain possible without XR.

## 7. Implementation increments

1. Publish a guest OS manifest and provider-neutral provisioning interface.
2. Build a read-only host/guest inventory adapter.
3. Add Quickemu/QEMU as an independently operable reference path with reproducible image metadata.
4. Add isolated test profiles for systemd-nspawn and one microVM backend.
5. Add conformance fixtures for guest compatibility, network isolation, resource caps, lifecycle, and cleanup.
6. Add agent/MCP and XR adapters only after core provisioning tests pass.

## 8. Evidence status

| Item | Status |
|---|---|
| Candidate tools and runtime distinctions recorded | Documented |
| Guest manifest and provisioning contract | Proposed |
| Reference VM implementation | Not implemented |
| Container/microVM comparative test matrix | Pending |
| MCP adapters and XR interface | Not implemented |
| Candidate source/license/security verification | Pending |
