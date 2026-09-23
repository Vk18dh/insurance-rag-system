# Frontend Design Blueprint

## 1. Current Frontend Architecture
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4, shadcn/ui
- **State Management**: React Context, SWR for data fetching
- **Core Integrations**: FastAPI Backend REST API via Bearer Tokens

## 2. Design Vision
The website will evolve from a standard dashboard into a **PREMIUM, MODERN, INTERACTIVE, TRUSTWORTHY, FUTURISTIC, and PROFESSIONAL** Insurance AI platform. The core aesthetic will rely on deep navy and dark blue tones, soft glassmorphism surfaces, subtle cyan/blue highlights, and a clean, spacious typographic hierarchy. It will employ a **hybrid 2D + 3D architecture**: functional 2D UI for navigation and data readability, combined with rich, interactive 3D WebGL experiences for immersion without sacrificing accessibility.

## 3. Page Inventory
1. **Landing Page (`/page.tsx`)**: High-impact marketing and entry point.
2. **AI Assistant (`/(chat)/layout.tsx`, `/(chat)/c/[id]/page.tsx`)**: The primary functional workspace.
3. **Login (`/login/page.tsx`)**: Secure authentication entry.
4. **Register (`/register/page.tsx`)**: New user onboarding.
5. **Error (`/error.tsx`, `/not-found.tsx`)**: Branded fallback states.

## 4. Landing Page
- **Hero**: "Trusted Knowledge. Smarter Decisions." / "Ask questions about insurance policies and get answers grounded in trusted insurance documents."
- **Interactive Earth**: The visual centerpiece (React Three Fiber).
- **Floating Insurance Concepts**: Interactive 3D/HTML nodes orbiting the Earth.
- **CTAs**: "Ask AI Now", "Explore Knowledge".
- **Sections**: Why Insurance AI? → How it Works (Ask, Retrieve, Verify, Answer) → Trusted Sources → Final CTA.

## 5. Interactive Earth
A stylized, dark-blue cinematic 3D globe using Three.js / React Three Fiber.
- **Lighting**: Elegant atmospheric glow, subtle geographic illumination.
- **Emphasis**: Subtle visual emphasis (e.g. slight glow) on India.
- **Performance**: Lazy-loaded, decoupled from 2D DOM blocking, optimized polygon count.

## 6. Mouse Interaction (Earth)
- Mouse movement interpolates a target rotation vector.
- The Earth naturally and smoothly follows the cursor using easing functions.
- Creates a parallax effect with atmospheric lighting and floating nodes.

## 7. Drag Interaction (Earth)
- Click-and-drag allows manual rotation.
- Incorporates inertia: upon release, the Earth gradually slows down before returning to its default state.

## 8. Idle Rotation (Earth)
- When no mouse movement or dragging is detected, the Earth slowly and elegantly rotates on its Y-axis.

## 9. Touch Interaction
- Mobile devices support touch-drag rotation and tap-to-interact for floating nodes.
- Touch events override idle rotation smoothly.

## 10. Floating Insurance Nodes
- Orbiting concepts: *Life Protection, Savings, Retirement, Family Protection, Policy Knowledge*.
- Clicking a node routes the user to the AI Assistant and populates (but does not auto-submit) a relevant question (e.g., "What does the policy say about life protection benefits?").

## 11. AI Assistant 3D
- A smaller, unobtrusive 3D visualization (e.g., an elegant energy orb or abstract core) located in the chat interface.
- Responds directly to the system's processing state.

## 12. Processing UX
Visualizes the backend waiting period (5-10s) with simulated, elegant UX stages:
- "Understanding your question" → "Searching insurance documents" → "Verifying evidence" → "Preparing your answer".
*(These are strictly UI animations to maintain engagement, not fake backend claims).*

## 13. Chat UX
- **User Messages**: Clear, right-aligned, distinct styling.
- **Assistant Messages**: Markdown-rendered, readable typography, integrated citations.
- **Suggested Follow-ups**: Actionable chips below the answer to drive continued engagement.

## 14. Citation UX
- Inline or cleanly appended source references.
- Raw UUIDs are hidden. Display features `document` name, `page`, and `confidence`.

## 15. Source Viewer
- Clicking a citation opens a slide-out drawer or modal.
- Displays the exact `content_snippet` retrieved by the RAG backend, ensuring the user can verify the ground truth.

## 16. Source Graph (Optional)
- A subtle 2D/3D visual node graph illustrating how retrieved sources feed into the final answer. *Must only use actual returned sources.*

## 17. Safe Refusal
- When `is_safe=False` or confidence is 0.0, display a calm, non-alarming message (e.g., "I couldn't find enough information...").
- Styled softly (yellow/orange warnings) rather than harsh red errors.

## 18. Ambiguity UX
- Prompts the user for clarification without simulating a crash.

## 19. Guardrail UX
- Calmly informs the user if a query violates system constraints, masking internal security implementation details.

## 20. Provider Failure UX (HTTP 503)
- "AI Services Unavailable" state. Provides a clean retry mechanism. Does not fake responses or HITL states.

## 21. HITL Status UX
- If a `review_task_id` is present, a subtle "Pending expert review" badge is displayed.

## 22. Conversation History
- Sidebar listing previous conversations.
- Supports creating new conversations and switching contexts.
- *(Delete is unsupported by backend and will be omitted).*

## 23. Login
- Premium LIC-styled authentication form.
- Subtle 3D/ambient background. Fully accessible keyboard navigation.

## 24. Registration
- Clean, trustworthy onboarding. Standard validation and loading states.

## 25. Error Pages
- Minimalist, branded 404/Error experiences with clear "Return to AI Assistant" actions.

## 26. Responsive Design
- **Desktop**: Full immersive 3D, sidebars, multi-column layouts.
- **Tablet**: Reduced WebGL complexity, responsive sidebars.
- **Mobile**: Touch-optimized Earth, single-column chat, hamburger navigation, simplified 3D elements.

## 27. Accessibility
- `prefers-reduced-motion` drastically reduces or disables 3D rotations/parallax.
- High contrast typography. `aria-live` regions for chat updates. Fully keyboard navigable.

## 28. Performance
- 3D elements dynamically imported (`next/dynamic`).
- Textures compressed. No blocking of the React main thread during initial page load. WebGL fallback to static gradients/images if context fails.

## 29. Component Architecture
- `components/3d/` (Earth, AssistantOrb)
- `components/chat/` (MessageFeed, ChatInput, Sidebar)
- `components/ui/` (Buttons, Inputs, Cards - standard 2D)

## 30. Design System
- **Primary**: Deep Navy, Dark Blue
- **Accent**: Cyan/Blue
- **Typography**: Inter/Geist (Modern, clean, legible)
- **Surfaces**: Glassmorphism (blur + semi-transparent dark backgrounds)

## 31. User Journeys
- **First Visit**: Lands → Interacts with Earth → Clicks Node → Registers/Logs in → Views pre-filled query → Submits → Views Citations.
- **Returning**: Logs in → Resumes Conversation → Queries → Reads Source Viewer.

## 32. Testing Requirements
- E2E testing for Login, Register, Query execution.
- Manual verification of Earth mouse-tracking, inertia, and touch interactions.
- Mobile layout validation.

## 33. Implementation Priorities
1. Pre-requisites (Dependencies, basic theme updates).
2. Login/Register Redesign.
3. Chat UI / Citations Redesign (Functional baseline).
4. Interactive Earth & Landing Page (The "Wow" factor).
5. 3D Assistant & Micro-interactions.
6. Performance & Accessibility Polish.

## 34. Unsupported/Future Features
- Real-time streaming (Backend is blocking).
- Profile management (No API).
- Conversation deletion (No API).
- End-user feedback loops (No API).
