📍 WHERE DONOR SEES MESSAGES FROM NGO
═══════════════════════════════════════════════════════════════════════

STEP-BY-STEP FLOW:

1️⃣  NGO SENDS MESSAGE TO DONOR
   ┌─────────────────────────────────┐
   │ NGO Dashboard or Medicine Page  │
   │                                 │
   │ 1. Searches medicine            │
   │ 2. Clicks "Contact Donor"       │
   │ 3. Types message in chat        │
   │ 4. Message SENT ✓               │
   └─────────────────────────────────┘
              ↓
      Message stored in Database
      (Conversation & Message models)


2️⃣  DONOR NOTIFICATION LOCATIONS
   
   Location A: NAVBAR (Top Right)
   ┌──────────────────────────────────────┐
   │ [Home] [Dashboard] [Search] [📧 Messages] ← Click Here!
   │                               ↑
   │                         Shows count if
   │                         unread messages
   └──────────────────────────────────────┘

   Location B: MESSAGES PAGE
   URL: /messages/
   ┌──────────────────────────────────────┐
   │ Messages                             │
   │ ─────────────────────────────────────│
   │ ┌──────────────────────────────────┐ │
   │ │ 💊 Medicine Name (Qty)           │ │
   │ │ Chatting with: NGO Name          │ │
   │ │ Last message: just now          │ │
   │ │ [Open Chat] ← Click to view msgs │ │
   │ └──────────────────────────────────┘ │
   │                                      │
   │ ┌──────────────────────────────────┐ │
   │ │ 💊 Another Medicine              │ │
   │ │ Chatting with: Another NGO       │ │
   │ │ Last message: 2 hours ago        │ │
   │ │ [Open Chat]                      │ │
   │ └──────────────────────────────────┘ │
   └──────────────────────────────────────┘

   Location C: CHAT DETAIL PAGE
   URL: /messages/{conversation_id}/
   ┌──────────────────────────────────────┐
   │ Chat: Medicine Name (Qty)            │
   │ ─────────────────────────────────────│
   │                                      │
   │ 📱 NGO Message appears HERE ✓        │
   │ [Left side, grey bubble]             │
   │                                      │
   │ NGO: "Hi, do you have this med?"    │
   │                                      │
   │ [Your reply here]                    │
   │ [Right side, blue bubble]            │
   │ You: "Yes, available now"           │
   │                                      │
   │ [Message Input Box]                  │
   │ [Send] [Request Location] [Share...] │
   └──────────────────────────────────────┘


HOW DONOR GETS NOTIFIED:

✅ METHOD 1: Check Navbar
   - Donor sees [📧 Messages] icon in navbar
   - If there are unread messages, badge shows count
   - Click icon → goes to /messages/

✅ METHOD 2: Check Messages Page
   - URL: http://localhost:8000/messages/
   - Shows ALL conversations (all medicines being discussed)
   - Each conversation shows:
     • Medicine name & quantity
     • NGO name (hidden: phone, email)
     • Last message timestamp
     • Unread message count (if any)

✅ METHOD 3: View Full Chat
   - Click "Open Chat" on any conversation
   - See complete message history
   - See NGO's messages in grey bubbles (left side)
   - Type reply and send

✅ METHOD 4: Enable Notifications (Future)
   - Could add email notifications
   - Could add browser push notifications
   - Could add SMS alerts


CURRENT MESSAGE VISIBILITY:

When NGO sends message:
├─ Message TYPE: text/location/location_request
├─ STORED IN: Conversation model (medicine + donor + ngo)
├─ MESSAGE VISIBLE TO:
│  ├─ NGO: in their Messages inbox ✓
│  └─ DONOR: in their Messages inbox (if they check) ✓
├─ HIDDEN FROM: Public (other NGOs/donors cannot see)
└─ PRIVACY: No email/phone shown, only username & role


EXAMPLE FLOW:

1. NGO "Hospital ABC" wants Paracetamol from Donor "John"
   
   NGO clicks: Donate Medicine → Medicine Detail → [Contact Donor (Chat)]
   
2. NGO types: "Hi, do you have Paracetamol 500mg? We need 100 strips."
   
   [Send] → Message stored in database
   
3. DONOR "John" must go to:
   
   a) Click [📧 Messages] in navbar
      OR
      b) Go to /messages/ directly
      OR
      c) Click Messages link in sidebar
   
4. Donor sees:
   ┌────────────────────────────────────┐
   │ Messages                           │
   ├────────────────────────────────────┤
   │ 💊 Paracetamol 500mg (100 units)  │
   │ Hospital ABC: "Hi, do you have..." │
   │ [Open Chat] ← Click                │
   └────────────────────────────────────┘
   
5. Donor clicks [Open Chat]
   
6. Donor sees the NGO's message:
   ┌────────────────────────────────────┐
   │ NGO Avatar │ Hospital ABC          │
   │            │ Hi, do you have       │
   │            │ Paracetamol 500mg?    │
   │            │ We need 100 strips.   │
   └────────────────────────────────────┘
   
7. Donor types reply:
   [Type message here...]
   
   Donor: "Yes, I have 100 strips available. When can you pickup?"
   
   [Send] ← Now NGO sees Donor's reply


WHERE TO FIND MESSAGES:

For Donor:
┌─────────────────────────────────────────────────────┐
│ 1. Top Navbar:  [📧 Messages] ← Click here first   │
│ 2. Direct URL: /messages/                          │
│ 3. After donation: Check Messages inbox regularly  │
│ 4. Phone: Would need to be notified manually       │
└─────────────────────────────────────────────────────┘

For NGO:
┌─────────────────────────────────────────────────────┐
│ Same as Donor:                                      │
│ 1. Top Navbar:  [📧 Messages] ← Click here first   │
│ 2. Direct URL: /messages/                          │
│ 3. Check for conversations & replies              │
└─────────────────────────────────────────────────────┘


FUTURE IMPROVEMENTS TO ADD:

1. 🔔 Email Notification
   - Send email to donor: "Hospital ABC wants to discuss Paracetamol"
   - Include link to message
   
2. 🔔 Browser Notification
   - Pop-up when new message arrives
   - Shows: "NGO sent you a message"
   
3. 🔔 Unread Badge in Navbar
   - Show [📧 Messages (2)] if 2 unread
   - Clear when viewed
   
4. ⏰ Last Seen Indicator
   - Show when each party last viewed chat
   - "Donor seen at 2:30 PM"
   
5. 💬 Typing Indicator
   - "NGO is typing..."
   - Real-time message updates


═══════════════════════════════════════════════════════════════════════

SUMMARY:

When NGO sends message to Donor:

🔸 Message saved in database
🔸 Donor can see in: [📧 Messages] navbar link
🔸 Shows in: /messages/ page
🔸 View full chat: /messages/{conversation_id}/
🔸 NO EMAIL/PHONE SHARED - Privacy protected ✓

DONOR MUST ACTIVELY CHECK MESSAGES
(Future: Add automatic notifications)

═══════════════════════════════════════════════════════════════════════
