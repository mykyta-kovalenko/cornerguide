from typing import List, Dict, Any

def get_golden_dataset() -> List[Dict[str, Any]]:
    return [
        {
            "question": "Are heel hooks legal for white belts?",
            "ground_truth": "No, heel hooks are not legal for white belts in IBJJF. They are prohibited for all belt levels below brown belt.",
            "federation": "IBJJF"
        },
        {
            "question": "What's the time limit for matches?",
            "ground_truth": "ADCC matches have a 10-minute regulation time, followed by overtime if needed.",
            "federation": "ADCC"
        },
        {
            "question": "Can you grab inside the gi pants during guard passing?",
            "ground_truth": "No, grabbing inside the gi pants is illegal in IBJJF and results in a penalty.",
            "federation": "IBJJF"
        },
        {
            "question": "Are wrist locks allowed for blue belts?",
            "ground_truth": "Yes, wrist locks are legal for blue and purple belts in IBJJF according to the rules update guide.",
            "federation": "IBJJF"
        },
        {
            "question": "How many points is a takedown worth?",
            "ground_truth": "A takedown is worth 2 points in ADCC scoring system.",
            "federation": "ADCC"
        },
        {
            "question": "Is it legal to pull guard immediately?",
            "ground_truth": "Yes, guard pulling is legal in IBJJF, but if done immediately without attempting a takedown, the opponent receives an advantage.",
            "federation": "IBJJF"
        },
        {
            "question": "What's the difference in scoring for mount?",
            "ground_truth": "IBJJF awards 4 points for mount, while ADCC awards 2 points for mount position.",
            "federation": "All"
        },
        {
            "question": "Are leg locks legal for all levels?",
            "ground_truth": "Yes, most leg locks including heel hooks are legal in ADCC for adult divisions, unlike IBJJF which restricts them by belt level.",
            "federation": "ADCC"
        },
        {
            "question": "Can you use the collar grip for more than 3 seconds without attacking?",
            "ground_truth": "No, in IBJJF you cannot maintain a collar grip for more than 3 seconds without progressing or attacking, or you'll receive a penalty.",
            "federation": "IBJJF"
        },
        {
            "question": "What happens if time runs out in regulation?",
            "ground_truth": "If regulation time ends without a submission or significant point difference, ADCC goes to overtime with specific rules for activity and penalties.",
            "federation": "ADCC"
        },
        {
            "question": "How are heel hooks handled differently between federations?",
            "ground_truth": "IBJJF restricts heel hooks to brown and black belts only, while ADCC allows heel hooks for all adult divisions. This is one of the major rule differences between federations.",
            "federation": "All"
        },
        {
            "question": "What are the main scoring differences between federations?",
            "ground_truth": "IBJJF uses a 4-2-3-1 point system (mount/back-4, guard pass/sweep-3, knee on belly/mount-2, advantage-1), while ADCC uses 2 points for takedowns, sweeps, and mount, with no advantages.",
            "federation": "All"
        },
        {
            "question": "How do time limits compare between federations?",
            "ground_truth": "IBJJF matches vary by belt level (5-10 minutes), while ADCC has standardized 10-minute matches for most divisions with overtime rules.",
            "federation": "All"
        },
        {
            "question": "Are there uniform differences between federations?",
            "ground_truth": "Yes, IBJJF has strict gi regulations for gi competitions, while ADCC is no-gi only with specific rashguard and shorts requirements.",
            "federation": "All"
        },
        {
            "question": "How is stalling treated differently between federations?",
            "ground_truth": "Both federations penalize stalling, but IBJJF uses advantages and penalties while ADCC has more aggressive stalling calls and uses negative points in overtime.",
            "federation": "All"
        }
    ]