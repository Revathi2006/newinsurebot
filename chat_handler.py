import json
from rag_retriever import ask_general

def load_script():
    with open("Calling Script.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

LINES = load_script()

class ChatHandler:
    def __init__(self):
        with open("customer_policies.json", "r", encoding="utf-8") as f:
            self.customers = json.load(f)
        self.step = 0
        self.customer = None
        self.waiting_for_reason = False
        self.payment_reason = None

    def _is_general_question(self, text):
        general_keywords = [
            "term insurance", "insurance", "policy", "premium",
            "benefit", "sum assured", "coverage", "claim",
            "maturity", "grace period", "due date", "what", "why", "how"
        ]
        return any(w in text for w in general_keywords)

    def _detect_intent(self, text):
        if any(w in text for w in ["yes", "sure", "okay", "agree"]):
            return "agree"
        if any(w in text for w in ["no", "not now", "later", "can't", "unable"]):
            return "refuse"
        if any(w in text for w in ["paid", "last week", "already"]):
            return "paid"
        if any(w in text for w in ["online", "cash", "cheque"]):
            return "payment_mode"
        return "other"

    def handle(self, msg: str) -> str:
        m = msg.strip().lower()

        # ✅ Handle general KB questions at any point
        if self._is_general_question(m):
            kb_answer = ask_general(msg)
            if self.step == 3 and self.waiting_for_reason:
                return f"{kb_answer} Now, could you share your reason for the delay in payment?"
            elif self.step == 3:
                return f"{kb_answer} Let's continue. Could you tell me your reason for the delay in payment?"
            elif self.step == 4:
                return f"{kb_answer} Moving on, do you know the benefits of your policy?"
            elif self.step == 6:
                return f"{kb_answer} Now, could you tell me if you'll pay online, cash, or cheque?"
            else:
                return kb_answer

        # Step 0: Identify name
        if self.step == 0:
            for c in self.customers:
                if c["name"].lower() in m:
                    self.customer = c
                    self.step = 1
                    return LINES[0].replace("{name}", c["name"])
            return LINES[0].replace("{name}", "sir/madam")

        # Step 1: Ask for time to talk
        if self.step == 1:
            intent = self._detect_intent(m)
            if intent == "agree":
                self.step = 2
                return LINES[1]
            else:
                return "May I know your relationship with the policyholder?"

        # Step 2: Show policy info
        if self.step == 2:
            c = self.customer
            self.step = 3
            return LINES[2].format(
                name=c["name"],
                policy_number=c.get("policynumber", "N/A"),
                purchase_date=c.get("purchasedate", "N/A"),
                due_date=c.get("duedate", "N/A"),
                premium=c.get("premium", "N/A"),
                product="Term Life"
            )

        # Step 3: Ask about reason for missing payment
        if self.step == 3:
            if self.waiting_for_reason:
                self.waiting_for_reason = False
                self.payment_reason = msg.strip()
                self.step = 4
                return f"I understand it was due to {self.payment_reason}. Let's go over the benefits of your policy."

            intent = self._detect_intent(m)

            if intent not in ["agree", "payment_mode", "paid"]:
                self.payment_reason = msg.strip()
                self.step = 4
                return f"I understand it was due to {self.payment_reason}. Let's go over the benefits of your policy."

            if intent == "refuse":
                self.waiting_for_reason = True
                return "I understand. Could you share your reason?"

            if intent == "agree":
                self.step = 6
                return "Great! Will you be paying online, cash, or cheque?"

            self.waiting_for_reason = True
            return "Could you tell me the reason for the delay in payment?"

        # Step 4: Ask if they know benefits
        if self.step == 4:
            if not self.payment_reason and m not in ["yes", "no"]:
                self.payment_reason = msg.strip()
                return f"I understand it was due to {self.payment_reason}. {LINES[4]}"
            self.step = 5
            return LINES[4]

        # Step 5: Offer solution
        if self.step == 5:
            self.step = 6
            return LINES[5]

        # Step 6: Ask about mode of payment
        if self.step == 6:
            intent = self._detect_intent(m)

            if intent == "other" and not self._is_general_question(m):
                self.payment_reason = msg.strip()
                return f"I understand it was due to {self.payment_reason}. Could you tell me if you'll be paying online, cash, or cheque?"

            if intent == "payment_mode":
                self.step = 7
                return LINES[6]

            if intent == "refuse":
                self.step = 9
                return "Alright, I understand you won't be paying right now."

            return "Could you tell me if you'll be paying online, cash, or cheque?"

        # Step 7: Thank for confirming payment mode
        if self.step == 7:
            self.step = 8
            return LINES[7]

        # Step 8: Acknowledge payment if mentioned
        if self.step == 8:
            intent = self._detect_intent(m)
            if intent == "paid":
                self.step = 9
                return LINES[8]
            else:
                self.step = 9
                return LINES[9]

        # Step 9: Ask about general queries or end
        if self.step >= 9:
            if self._is_general_question(m):
                return ask_general(msg)
            self.step = 99
            return LINES[-1]

        return "Could you please elaborate?"
