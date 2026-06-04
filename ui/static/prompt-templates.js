// Prompt template library for the welcome block.
// Each entry: { category, title, prompt }
// Categories appear in the order they first occur in this array.
// Loaded as a plain <script> before app.js — exposes window.PROMPT_TEMPLATES.

window.PROMPT_TEMPLATES = [
  // Getting Started — onboarding questions, no placeholders. Click → send-ready.
  { category: 'Getting Started', title: 'What can I ask?',
    prompt: 'What kinds of IAM questions can you help me with? Give me a short overview of your capabilities and the data you can query.' },
  { category: 'Getting Started', title: 'Glossary: BRT, BC, App',
    prompt: 'Explain the IAM concepts I will encounter most often: Business Role Template (BRT), Business Catalog, IAM App, Restriction Type. Use plain language.' },
  { category: 'Getting Started', title: 'What is SoD?',
    prompt: 'Explain Segregation of Duties (SoD) in this IAM system: what it means, why it matters, and how it shows up in catalogs and authorization objects.' },
  { category: 'Getting Started', title: 'How do roles work?',
    prompt: 'Walk me through how a Business Role Template gets composed from Business Catalogs and apps, and how those map to PFCG roles in SAP.' },

  // General
  { category: 'General', title: 'App → Catalog mapping',
    prompt: 'List all catalogs that include app <APP_ID>.' },
  { category: 'General', title: 'Restriction type coverage',
    prompt: 'Check restriction type coverage for <BC_ID>.' },
  { category: 'General', title: 'BRT catalog tree',
    prompt: 'Show the full catalog tree for Business Role Template <BRT_ID>.' },
  { category: 'General', title: 'Auth object usage',
    prompt: 'Find all apps that use authorization object <AUTH_OBJECT>.' },

  // Finance — Accounts Payable
  { category: 'Finance — AP', title: 'App auth analysis',
    prompt: 'For IAM App ID <APP_ID>, show all active authorization object instances and their field values.' },
  { category: 'Finance — AP', title: 'AP payment flow SoD',
    prompt: 'For the AP payment run flow (F0770_TRAN → F0771_TRAN → F0673A_TRAN), trace auth objects and confirm SoD between proposal, revision, and approval.' },

  // Finance — Accounts Receivable
  { category: 'Finance — AR', title: 'AR clearing & incoming payment',
    prompt: 'For AR clearing (F0773_TRAN) and incoming payment posting (F1345_TRAN), validate the authorization setup against expected activities.' },
  { category: 'Finance — AR', title: 'AR dunning SoD check',
    prompt: 'For AR, verify that dunning and incoming payment posting are not both held by a single role without oversight.' },

  // Finance — General Ledger
  { category: 'Finance — GL', title: 'GL posting controls',
    prompt: 'For the GL journal entry flow (post / park / verify), trace auth objects F_BKPF_BUK, F_BKPF_BLA, F_BKPF_KOA and confirm posting controls.' },
  { category: 'Finance — GL', title: 'Activity set check',
    prompt: 'For IAM App ID <APP_ID>, verify whether the activity set is aligned with the app\'s intended business purpose.' },

  // Finance — Bank Accounting
  { category: 'Finance — BA', title: 'Bank statement health check',
    prompt: 'For the bank statement processing flow, run a full IAM health check including authorization objects, activity sets, catalog assignments, and BRT coverage.' },

  // Treasury IAM
  { category: 'Treasury and Risk Management', title: 'FOE/BOE SoD validation',
    prompt: 'For app <APP_ID>, validate whether it is compliant with FOE or BOE SoD rules.' },
  { category: 'Treasury and Risk Management', title: 'Catalog split analysis',
    prompt: 'Analyze SAP_TC_FIN_TRM_COMMON and propose the FOE/BOE split — which apps go where?' },
  { category: 'Treasury and Risk Management', title: 'Hedge request SoD',
    prompt: 'For app <APP_ID>, validate T_TOE_HR values against MOE and Accountant forbidden combinations.' },
  { category: 'Treasury and Risk Management', title: 'BRT footprint',
    prompt: 'For Business Role Template <BRT_ID>, show the full catalog and app footprint.' },

  // Cash Management
  { category: 'Cash Management', title: 'Activity set completeness',
    prompt: 'For IAM App ID <IAM_APP_ID>, verify whether the authorization activity set is complete and aligned with the intended business process.' },
  { category: 'Cash Management', title: 'Submit/Approve SoD',
    prompt: 'For IAM App ID <IAM_APP_ID>, analyze whether submit and approve capabilities are properly segregated across applications and roles.' },
  { category: 'Cash Management', title: 'Four-eyes catalog check',
    prompt: 'For Business Catalog <BC_ID>, identify whether any access combination violates the four-eyes principle or introduces SoD risks.' },
  { category: 'Cash Management', title: 'IAM health check',
    prompt: 'For IAM App ID <IAM_APP_ID>, run a full IAM health check including authorization objects, activity sets, catalog assignments, and BRT coverage.' },
];
