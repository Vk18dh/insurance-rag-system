# Stage 10 Implementation Plan

## 1. Stage 10 Objective
To complete the **Feature-Based Review Workflow** by ensuring the User Website correctly fetches and displays the current state of escalated RAG responses (ReviewTasks) while maintaining strict application separation.

## 2. Authoritative Requirements
- "User sees review status" (`docs/06_IMPLEMENTATION_PLAN_FINAL.md`)
- "No user redirect to Management" (`docs/06_IMPLEMENTATION_PLAN_FINAL.md`)
- "Backend → User Website" workflow closure (`docs/06_IMPLEMENTATION_PLAN_FINAL.md`)

## 3. Current State
- The backend successfully triggers automated escalation (via `query.py`).
- The Management Website Expert UI successfully handles ReviewTasks (Approve/Correct).
- The User Website receives a `confidence_score` but does not know if a `ReviewTask` was created and cannot poll for its status.

## 4. Missing Functionality
1. The backend needs to return the `review_task_id` or initial review state during a `query` response.
2. The backend needs an endpoint for the User Website to poll the `ReviewTask` status by conversation.
3. The User Website needs UI components to indicate "Pending Expert Review", "Expert Approved", or "Expert Corrected (with updated answer)".

## 5. Architecture
- The existing PostgreSQL architecture will not change.
- Phase 1 and Phase 2 remain fully frozen.
- Only the FastAPI adapter and User Next.js application will be modified.

## 6. Files to Modify
- `backend/app/schemas/api.py`: Add `review_task_id` and `review_status` to `QueryResponse`.
- `backend/app/routers/query.py`: Assign `message_id` to the created `ReviewTask` and return the `review_task_id` in the `QueryResponse`.
- `backend/app/routers/conversations.py`: Add a polling endpoint to fetch review tasks for a conversation.
- `frontend/lib/api-client.ts`: Update schemas and add the polling function.
- `frontend/components/answer-display.tsx`: Update UI to show the current review state.
- `frontend/components/chat/chat-interface.tsx`: Add polling logic.

## 7. Files to Create
- `frontend/components/review-status-banner.tsx` (Optional, if extracting UI).

## 8. Database Changes
None. The `ReviewTask` schema is already capable. We just need to ensure `message_id` is populated correctly.

## 9. API Changes
- Modified: `POST /api/v1/query` (Returns `review_task_id` if escalated).
- New: `GET /api/v1/conversations/{id}/reviews` (Returns the statuses of tasks).

## 10. Frontend Changes
- The `frontend/` Next.js application will implement a polling mechanism or handle the new API payload to update the user with the expert's decision.

## 11. Docker Changes
None.

## 12. Security Considerations
- The new polling endpoint must be protected by the existing `get_current_user` dependency to ensure users can only poll reviews for their own conversations.

## 13. Testing Strategy
- Add unit tests in `backend/app/tests/test_conversations_api.py` for the new polling endpoint.
- Verify end-to-end that a corrected answer replaces the displayed answer in the User Website.

## 14. Regression Strategy
- Run all existing `pytest` backend tests to ensure `query.py` still operates perfectly for non-escalated queries.

## 15. Rollback Strategy
- Discard Git changes on `frontend/` and `backend/`.

## 16. Risks
- Potential UI state mismatch if polling happens before the `ReviewTask` is fully committed.
- Expert's `corrected_answer` must securely override the `final_answer` in the UI.

## 17. Dependencies
- Dependent on Stage 9 being fully intact.

## 18. Exact Implementation Sequence
1. Update `QueryResponse` schema and `query.py` to return the task ID.
2. Create the `GET /conversations/{id}/reviews` endpoint.
3. Update `frontend` `api-client.ts`.
4. Update `answer-display.tsx` and `chat-interface.tsx` to handle polling and display expert corrections.
5. Execute full E2E manual test.

## 19. Verification Plan
- Send an out-of-domain query from the User Website.
- See "Pending Expert Review" on the User Website.
- Log in as Expert on Management Website, submit a Correction.
- Verify the User Website dynamically updates to show the Corrected answer.

## 20. Definition of Done
- User Website displays real-time review status without page reload (via polling).
- Expert corrections successfully overwrite the displayed UI text on the User Website.
- No navigation links to Management exist on the User Website.
