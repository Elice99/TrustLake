# TrustLake — Product Requirements Document

- **Owner:** Elice Bassey
- **Version:** 2.0
- **Status:** Draft — Pre-MVP
- **Product Type:** Free, open-access data science workspace
- **Primary Users:** Data professionals
- **Core Audience:** Data Analysts, Data Scientists, ML Engineers, BI/Analytics Professionals
- **Product Philosophy:** Build a serious, portfolio-grade product using free/open-source technology
- **AI Architecture:** Provider-agnostic
- **AI:** Optional — user-selectable supported free AI models/providers
- **Current Build Stage:** Stage 1 — Landing Page Complete
- **Next Build Stage:** Stage 2 — Core Backend Foundation

---

## 1. Product Definition

TrustLake is a data intelligence workspace that helps data professionals move from raw data to trusted analysis and machine-learning predictions in one place.

A user can bring a dataset into TrustLake and:

**Profile → Clean → Prepare → Analyze → Build ML Models → Evaluate → Predict**

The platform does not automatically manipulate the user's data or make decisions on their behalf. Instead, TrustLake:

- examines the data,
- identifies potential problems,
- explains what it finds,
- recommends possible approaches when requested,
- lets the user decide what to apply,
- preserves the original data,
- records transformations,
- evaluates analytical and ML readiness,
- and provides reproducible results.

The intended experience is:

> "Wait... this thing checked my data, told me whether I could trust it, cleaned it, showed me what was happening in the data, and then built and compared the right ML models for me."

That is the product experience TrustLake should work toward.

---

## 2. Product Vision

TrustLake should become a single workspace for data professionals where they can take a dataset from raw input to useful analytical or machine-learning output without constantly moving between different tools.

The first version should not attempt to replace every professional data tool. Instead, it should prove one complete workflow extremely well:

> Can TrustLake take messy real-world data and help a data professional turn it into trustworthy analysis or a usable ML model?

The product should feel significantly more capable than a generic CSV cleaner, while remaining technically realistic to build on a personal computer using free/open-source technologies.

---

## 3. The Governing Principle

### The One Rule

**If a decision doesn't serve "can I trust this dataset," it waits.**

Every feature must pass three questions:

- Does it make the data more trustworthy, understandable, or usable?
- Would a real data professional notice if it were missing?
- Can the smaller version be built first?

If the answer is not yes to all three, the feature goes into the parking lot. This rule applies even when the feature sounds impressive.

---

## 4. What TrustLake Is

- A data profiling workspace.
- A data cleaning and preparation environment.
- A data quality/trust engine.
- An exploratory data analysis environment.
- An intelligent analytics assistant.
- A lightweight ML experimentation environment.
- A model evaluation workspace.
- A prediction workspace.
- An optional AI-assisted data science environment.

---

## 5. What TrustLake Is Not

TrustLake v1 is not:

- A full enterprise data governance platform.
- A metadata catalog.
- A Databricks replacement.
- A full AutoML platform.
- A Kubernetes-scale ML platform.
- A replacement for specialised production ML infrastructure.
- A multi-agent AI platform.
- A generic chatbot.
- An automatic data-cleaning machine that changes user data without permission.

These may become future possibilities, but they are not required to make v1 successful.

---

## 6. Target Users

### Primary

**Data Analysts** — users who need to:
- inspect datasets,
- clean data,
- perform EDA,
- generate insights,
- answer business questions,
- export analysis-ready datasets.

**Data Scientists** — users who need to:
- prepare data,
- explore relationships,
- identify useful features,
- build regression/classification models,
- compare models,
- tune models,
- evaluate performance,
- generate predictions.

**ML Engineers / ML Practitioners** — users who want:
- reproducible preprocessing,
- model experimentation,
- evaluation,
- model storage,
- prediction endpoints,
- model comparison.

**BI / Analytics Professionals** — users who need to understand whether a dataset is trustworthy before building reports or dashboards.

---

## 7. The Core TrustLake Experience

The platform should have three primary working areas:

- **Data Cleaning & Preparation:** Understand → Clean → Prepare → Export
- **Analytics:** Profile → EDA → Insights → Business Questions
- **Machine Learning:** Problem Definition → Preparation → Model Selection → Training → Evaluation → Tuning → Prediction

These areas are connected rather than isolated. A user can move:

- Cleaning → Analytics
- or Cleaning → ML
- or Analytics → ML
- or eventually: ML → Prediction

---

## 8. Initial Platform Flow

When the user enters TrustLake, they should already understand what they want to accomplish.

The main workspace presents clear actions:

```
TRUSTLAKE
What do you want to do?
[ Clean & Prepare Data ]
[ Analyze Data ]
[ Build ML Model ]
[ Make Predictions ]
```

The user chooses the workflow. TrustLake then adapts the experience to that purpose.

---

## 9. Dataset Profiling

Regardless of whether the user enters through Cleaning, Analytics, or ML, uploading a dataset should trigger profiling.

Profiling does not automatically clean anything. It simply tells the user what TrustLake sees.

**Example**

```
DATASET PROFILE
Rows                15,000
Columns             24
Missing values      6.2%
Duplicate rows       143
Potential outliers    87
Type issues            3
Constant columns       2
Potential IDs           4
```

Additional information:

- column types,
- unique values,
- missing percentages,
- distributions,
- duplicates,
- suspicious values,
- cardinality,
- basic statistics,
- correlations where appropriate,
- potential target variables,
- potential identifiers.

---

## 10. Trust Score

The Trust Score remains one of the defining components of TrustLake.

It must be: **Deterministic. Reproducible. Explainable.** AI must never generate the score.

**Example**

```
TRUST SCORE
82 / 100
GOOD

Completeness   92
Uniqueness     71
Consistency    88
Freshness      76
```

The score should explain:

- what affected it,
- how strongly,
- which columns contributed,
- what evidence supports the finding.

The exact scoring algorithm should remain transparent and version-controlled.

---

## 11. Data Cleaning & Preparation

TrustLake should support cleaning for both analytics and machine learning. This is important because the requirements are not identical.

**Analytics preparation** may involve:

- missing values,
- duplicates,
- inconsistent categories,
- incorrect types,
- date formatting,
- unnecessary columns,
- outliers,
- inconsistent labels.

**ML preparation** may additionally involve:

- target selection,
- feature selection,
- encoding,
- scaling,
- train/test splitting,
- validation splitting,
- class imbalance handling,
- leakage detection,
- preprocessing pipelines.

---

## 12. Human-Controlled Cleaning

TrustLake must not automatically change data simply because it found a problem.

The workflow should be:

```
TrustLake detects issue
   ↓
User sees issue
   ↓
User can inspect it
   ↓
User requests recommendation OR chooses manually
   ↓
TrustLake recommends method
   ↓
User accepts / rejects / modifies
   ↓
Transformation applied
```

Users should have options such as:

- Apply recommendation
- Ignore
- Choose another method
- Configure manually
- Cancel

---

## 13. Original Data Preservation

The original dataset must remain untouched. Every transformation should operate on a derived working version.

Conceptually:

```
Original Dataset
   │
   ├── Step 1
   │
   ├── Step 2
   │
   ├── Step 3
   │
   ▼
Current Working Dataset
```

The user must be able to:

- undo a transformation,
- cancel a step,
- return to an earlier state,
- compare before/after,
- inspect what changed.

This is critical to TrustLake's trust model.

---

## 14. Transformation History

Every transformation should have a record:

```
STEP 04
Action:   Filled missing values
Column:   age
Method:   Median
Before:   1,204 missing
After:    0 missing
Applied:  23 Aug 2026
Status:   Applied
```

This eventually creates a reproducible transformation pipeline.

---

## 15. Analytics Workspace

The Analytics section should contain two layers.

### Traditional EDA

TrustLake should generate standard analytical outputs such as:

- distributions,
- histograms,
- box plots,
- categorical distributions,
- correlation matrices,
- scatter plots,
- missing-value analysis,
- summary statistics,
- time trends.

The user should be able to select variables and customize analysis.

---

## 16. Intelligent Analytics

AI should be optional. TrustLake should initially show the analytical results without requiring AI.

The user can then select **Generate Insights**. The AI interprets the existing analytical evidence.

**Example**

> "Revenue increased 18% during Q3, but the increase was concentrated in two product categories. The remaining categories remained relatively stable."

The AI must base its explanation on actual computed statistics. It must not invent analytical findings.

---

## 17. Conversational Analytics

Users should also be able to ask questions.

**Examples**

> "Which product category contributed most to revenue growth?"
>
> "Is there evidence that customer age is related to purchase value?"

TrustLake computes the relevant analysis and the AI explains the result. The AI is therefore an analytics assistant, not the analytics engine itself.

---

## 18. Business Problem Input

A user should eventually be able to provide a business question or problem.

**Example**

> "Management wants to know why customer retention dropped last quarter."

TrustLake can use the available dataset and analytical capabilities to identify relevant analyses.

The system should explain:

- what it examined,
- what it found,
- what evidence supports the finding.

Again, the AI should not fabricate conclusions.

---

## 19. ML Workspace

The ML section is a major addition to the product. However, v1 should deliberately support only **Regression and Classification**.

Other ML problem types belong in the future roadmap.

---

## 20. ML Problem Definition

Before building a model, the user identifies what they are trying to predict.

**Example**

```
What are you trying to predict?
[ Regression ]
Target column: [ house_price ] ▾
Prediction objective: Predict future house prices
```

Or:

```
[ Classification ]
Target: [ customer_churn ] ▾
Objective: Predict whether a customer will churn
```

This allows TrustLake to show only models relevant to the problem.

---

## 21. Beginner and Expert Modes

TrustLake should accommodate different skill levels.

### Beginner

The user can say: "I don't know which model to use."

TrustLake can recommend appropriate models based on:

- problem type,
- target characteristics,
- dataset size,
- feature types,
- evaluation requirements.

The user remains in control.

### Expert

The user can directly select:

**Regression**
- ☐ Linear Regression
- ☐ Ridge
- ☐ Random Forest
- ☐ Gradient Boosting

**Classification**
- ☐ Logistic Regression
- ☐ Random Forest
- ☐ Gradient Boosting
- ☐ XGBoost

The exact initial model list should be kept manageable and based on what can run reliably on the available hardware.

---

## 22. Train / Validation / Test Configuration

TrustLake should manage dataset splitting. Users can choose:

- **Option A** — Train / Test: 80 / 20
- **Option B** — Train / Validation / Test: 70 / 15 / 15

TrustLake should recommend a reasonable configuration when the user does not know what to choose. The final choice remains with the user.

---

## 23. ML Data Readiness Gate

Before training, TrustLake should evaluate whether the dataset is suitable for the selected ML task.

**Example**

```
ML READINESS
Overall: 74 / 100

⚠ Warning   Target column contains 18% missing values.
⚠ Warning   Potential data leakage detected.
✓ OK        No duplicate rows detected.
✓ OK        Target variable identified.
⚠ Warning   Class imbalance: 82 / 18
```

The user should be able to decide whether to proceed. This prevents users from unknowingly training models on obviously problematic data.

---

## 24. Model Training

After the user confirms the configuration, TrustLake trains the selected models.

**Example — Regression**

```
MODEL COMPARISON
Random Forest        R²  0.81
Gradient Boosting     R²  0.84
Linear Regression     R²  0.68
```

**Example — Classification**

```
MODEL COMPARISON
Random Forest         Accuracy  91%
Logistic Regression   Accuracy  84%
Gradient Boosting     Accuracy  93%
```

The exact evaluation metrics should depend on the problem.

---

## 25. Model Evaluation

TrustLake should show appropriate metrics.

**Regression** — potential metrics: MAE, MSE, RMSE, R², adjusted R² where appropriate.

**Classification** — potential metrics: Accuracy, Precision, Recall, F1, ROC-AUC, confusion matrix.

The exported model report should contain the important evaluation results.

---

## 26. Feature Importance

Where the selected model supports meaningful feature importance, TrustLake should show it.

**Example**

```
FEATURE IMPORTANCE
1. Income               34.2%
2. Age                  21.8%
3. Purchase Frequency   16.4%
4. Tenure                11.2%
5. Region                 8.1%
```

The visualization should accompany the numerical results. For models where traditional feature importance is inappropriate, TrustLake should use an appropriate interpretation method rather than pretending every model has the same type of importance.

---

## 27. Model Selection

TrustLake should compare models rather than simply hiding the alternatives. The user can:

- choose a model manually,
- compare available models,
- select the recommended model,
- reject the recommendation.

The system should explain why a model was recommended.

---

## 28. Hyperparameter Tuning

Hyperparameter tuning belongs in v1. However, it should be designed with hardware limitations in mind.

The user can configure:

- tuning method,
- search space,
- number of iterations,
- evaluation metric,
- time/resource limits.

TrustLake should provide reasonable defaults.

**Example**

```
HYPERPARAMETER TUNING
Current:         R² = 0.81
Tuning budget:   [ 20 iterations ]
Metric:          [ R² ]
[ Start tuning ]
```

The goal is not to build a massive AutoML system. It is to provide controlled, useful model improvement.

---

## 29. AI as ML Assistant

AI should be optional. If no AI provider is configured, the ML system must still work.

The AI can explain:

- why a model performed poorly,
- why one model outperformed another,
- what a metric means,
- what a hyperparameter does,
- what feature importance suggests,
- what the user might try next.

**Example**

> "Random Forest performed better than Linear Regression because the relationship between the predictors and target appears to be non-linear."

The AI should base these explanations on actual model outputs.

---

## 30. User-Selectable AI

TrustLake should not lock users into one AI vendor. The architecture should use an AI provider interface.

**Example**

```
AI Provider
○ Gemini
○ Groq
○ Other supported providers
○ No AI
```

The user chooses what they want to use from the providers TrustLake supports. This gives TrustLake:

- provider independence,
- lower costs,
- flexibility,
- easier experimentation,
- better privacy options,
- no architectural dependency on one company.

---

## 31. AI Safety Boundary

The AI must never:

- determine the Trust Score,
- modify the original dataset,
- execute arbitrary Python,
- execute arbitrary SQL,
- change a model without permission,
- deploy a model without permission,
- approve its own recommendation,
- silently modify preprocessing,
- silently change hyperparameters.

The architecture should instead be:

> **Computers calculate. Rules decide. AI explains and recommends. Humans control.**

---

## 32. Saved Models

Once a user finishes training a model, TrustLake should save the model configuration and artifact. The user should not have to retrain the model every time they want a prediction.

Saved model information should include:

- model name,
- problem type,
- target,
- features,
- preprocessing steps,
- model type,
- hyperparameters,
- evaluation metrics,
- training dataset information,
- training timestamp,
- model version.

---

## 33. Prediction Workspace

After validation, users can enter a dedicated prediction area.

**Example**

```
MAKE PREDICTION
Select model: [ Customer Churn Model ] ▾
Upload new dataset: [ Upload CSV ]
[ Predict ]
```

The system uses the saved preprocessing and model configuration. The user receives:

```
Prediction complete.
10,000 predictions generated.
[ View Results ]
[ Download CSV ]
```

---

## 34. Multiple Models

Users may build multiple models for different purposes.

**Example**

```
MY MODELS
Customer Churn Model
House Price Model
Sales Forecast Classifier
Loan Default Model
```

The user chooses which model to use for each prediction task.

---

## 35. Analytics → ML Transition

Analytics and ML should not be separate silos. After discovering patterns during EDA, the user should be able to move directly into ML.

**Example**

```
Analytics finding:
Customer tenure appears strongly associated with churn.
[ Build Classification Model ]
```

This creates a natural **Analyze → Model** workflow.

---

## 36. Cleaning → Analytics / ML Transition

Likewise:

```
DATA CLEANING COMPLETE
Your dataset is now prepared.
What would you like to do?
[ Analyze Dataset ]
[ Build ML Model ]
[ Export Dataset ]
```

This is one of the strongest UX ideas in the entire product. The user does not have to start a completely new workflow.

---

## 37. Export

Users should be able to export:

**Data** — cleaned dataset, prepared dataset, transformed dataset.

**Analytics** — statistics, charts, insights, analytical report.

**ML** — model evaluation, feature importance, confusion matrix, predictions, model configuration, preprocessing information.

The important evaluation information should always accompany exported ML results.

---

## 38. Reproducibility

TrustLake should preserve enough information to reproduce an experiment.

For each ML experiment:

```
Experiment
├── Dataset
├── Dataset version
├── Cleaning steps
├── Features
├── Target
├── Split configuration
├── Model
├── Hyperparameters
├── Evaluation
└── Timestamp
```

This is essential for a serious data-science product.

---

## 39. Data Versioning / Undo

TrustLake should preserve the original dataset and create derived versions.

**Example**

```
Dataset v1
   ↓  Removed duplicates
Dataset v2
   ↓  Filled missing values
Dataset v3
   ↓  Encoded categories
Dataset v4
```

Users should be able to return to earlier versions.

---

## 40. Architecture

The architecture should remain intentionally simple.

```
TRUSTLAKE
   │
   ┌──────────┴──────────┐
   │                      │
DATA WORKSPACE      AI ASSISTANT
   │                      │
   ┌───────┼────────┐     │
   │       │        │     │
 CLEAN  ANALYTICS   ML  AI Provider
   │       │        │    Interface
   │       │        │       │
   │       │        │  ┌────┴────┐
   │       │        │  │         │
   │       │        │ Gemini    Groq
   │       │        │
   └───────┼────────┘
           │
      TRUST ENGINE
           │
   ┌───────┴────────┐
   │                 │
Profiling      Data Quality
   │                 │
   └───────┬────────┘
           │
      PostgreSQL
           │
     Object Storage
```

---

## 41. Recommended Technical Architecture

### Frontend
- React
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Recharts

Next.js is recommended because the application will eventually have multiple connected workspaces, routes, model pages, prediction pages, and dashboard-like views.

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL

### Data Processing

**Primary:** pandas, NumPy, scikit-learn

**Optional escape hatch:** DuckDB

TrustLake should not introduce Spark or distributed processing until actual datasets demonstrate that it is necessary.

---

## 42. ML Stack

Initial ML framework: **scikit-learn**

Models should initially focus on:

**Regression**
- Linear Regression
- Ridge/Lasso where appropriate
- Random Forest Regressor
- Gradient Boosting Regressor

**Classification**
- Logistic Regression
- Random Forest Classifier
- Gradient Boosting Classifier

Additional models can be introduced after the basic workflow is stable. XGBoost can remain an optional extension if the local environment and dependency footprint make sense.

---

## 43. AI Architecture

The AI interface should look conceptually like:

```python
class AIProvider:
    def explain_issue(...):
        ...
    def summarize_profile(...):
        ...
    def generate_insight(...):
        ...
    def recommend_cleaning(...):
        ...
    def explain_model(...):
        ...
    def recommend_model(...):
        ...
    def explain_prediction(...):
        ...
```

Initial implementations:

- `GeminiProvider`
- `GroqProvider`

The product must also support `NoAIProvider`. That is important. TrustLake must remain functional without AI.

---

## 44. AI Data Boundary

Because free AI providers may have different data-handling policies, TrustLake should make AI usage explicit.

The platform should eventually show something similar to:

```
AI ASSISTANCE
AI is optional.
Your dataset can be analyzed without AI.
If you enable AI assistance, selected information
may be sent to your chosen AI provider.
[ Continue without AI ]
[ Enable AI ]
```

The provider-specific privacy implications should be clearly communicated.

For development, use:

- synthetic data,
- anonymized data,
- public datasets,
- non-confidential datasets.

Do not casually send real confidential business data through free AI APIs.

---

## 45. Database

PostgreSQL should store:

- users,
- datasets,
- dataset versions,
- profiling results,
- trust scores,
- transformations,
- experiments,
- models,
- model versions,
- predictions,
- audit events,
- AI provider configuration.

Large uploaded files and model artifacts should be stored separately in object storage rather than inside PostgreSQL.

---

## 46. Storage

**For local development:**
- Docker volume
- local object storage such as MinIO if needed

**For deployment later:**
- S3-compatible object storage.

Do not introduce a complicated cloud architecture until necessary.

---

## 47. Security

Minimum requirements:

- environment variables for secrets,
- `.env` excluded from Git,
- no API keys in frontend code,
- original data protected from accidental modification,
- AI access restricted through backend-controlled interfaces,
- audit logging,
- file validation,
- upload size limits.

---

## 48. Auditability

TrustLake should record important events such as:

- Dataset uploaded
- Dataset profiled
- Cleaning recommendation generated
- Cleaning operation approved
- Cleaning operation applied
- Cleaning operation undone
- Trust Score generated
- Analytics generated
- ML experiment started
- Model trained
- Model selected
- Hyperparameters changed
- Model saved
- Prediction generated
- AI provider used

This is not about building an enterprise governance platform. It is about making the product trustworthy and reproducible.

---

## 49. Performance Philosophy

TrustLake is initially being built on a personal computer. Therefore:

> Optimize for useful datasets, not imaginary petabyte workloads.

The first version should handle realistic CSV datasets comfortably. When performance becomes a genuine problem, the architecture can evolve. Do not build distributed infrastructure simply because enterprise products use it.

---

## 50. V1 Feature Boundary

### Included

**Data**
- CSV upload
- profiling
- Trust Score
- data cleaning
- data preparation
- transformations
- undo/history
- export

**Analytics**
- EDA
- charts
- statistics
- generated insights
- conversational analytical questions
- business problem input

**Machine Learning**
- regression
- classification
- model selection
- model comparison
- train/test splitting
- train/validation/test option
- evaluation
- feature importance
- hyperparameter tuning
- saved models
- prediction interface
- prediction export

**AI**
- optional
- Gemini
- Groq
- provider abstraction
- user selection
- recommendations on request
- analytics assistant
- ML assistant

---

## 51. Coming Soon / Future

The frontend may mention future capabilities without implementing them.

Potential future areas:

- clustering,
- time-series forecasting,
- anomaly detection,
- NLP,
- deep learning,
- AutoML,
- additional connectors,
- database connectors beyond PostgreSQL,
- model deployment,
- experiment collaboration,
- scheduled pipelines,
- advanced model monitoring,
- model explainability expansion,
- additional AI providers.

These should be visibly marked **Coming Soon**, not presented as currently available.

---

## 52. Explicitly Out of Scope for V1

Do not quietly introduce:

- Kafka
- Kubernetes
- Spark
- distributed compute
- multiple autonomous agents
- MCP as a requirement
- metadata catalog
- lineage platform
- enterprise governance
- enterprise compliance suite
- multi-tenant SaaS architecture
- custom rule-builder platform
- SDK
- CLI
- VS Code extension
- Power BI plugin
- dbt integration
- Airflow integration
- massive AutoML
- deep-learning platform
- production-scale model serving infrastructure

These belong in the parking lot.

---

## 53. V1 Success Criteria

TrustLake v1 should be considered successful if a data professional can:

1. Upload a genuinely messy dataset.
2. Understand its condition through profiling and Trust Score.
3. Clean and prepare it without losing the original.
4. Undo or modify transformations.
5. Perform meaningful EDA.
6. Generate evidence-based analytical insights.
7. Define an ML problem.
8. Prepare the dataset for that problem.
9. Train appropriate regression/classification models.
10. Compare their performance.
11. Tune a selected model.
12. Save the model.
13. Upload new data.
14. Generate predictions.
15. Download the results.

And critically: **the entire workflow should happen inside TrustLake.** The user shouldn't have to leave TrustLake halfway through the process to use another platform for a core task that TrustLake claims to support.

---

## 54. The Product's Real Differentiator

I would not market TrustLake as:

> "An AI-powered data cleaning platform."

That's too generic. I would also avoid:

> "An AI-powered AutoML platform."

That puts you into a crowded category immediately.

The stronger positioning is:

> TrustLake helps data professionals turn messy data into trusted analysis and machine-learning predictions.

And the experience is:

```
TRUSTLAKE
DATA
 │
 ▼
┌───────────┐
│   TRUST   │
│  PROFILE  │
└─────┬─────┘
      │
      ▼
┌───────────┐
│  CLEAN &  │
│  PREPARE  │
└─────┬─────┘
      │
 ┌────┴────┐
 ▼         ▼
┌────────┐ ┌────────┐
│ANALYTICS│ │   ML   │
└────┬────┘ └────┬───┘
     │            │
     ▼            ▼
 INSIGHTS      MODELS
                  │
                  ▼
             PREDICTIONS
```

That is much more interesting than "another data cleaner."

---

## 55. The TrustLake Promise

The simplest way I would describe the final product is:

> TrustLake checks your data before you trust it. Then it helps you prepare it, understand it, model it, and use it.

Or, for the more memorable product experience:

> **Check it. Clean it. Understand it. Model it. Predict with it.**

And the deeper product philosophy remains:

> **Trust first. Intelligence second. Decisions last.**

---

## 56. Updated Build Direction

This also means our old 9-stage roadmap needs to change. The landing page is still correctly Stage 1, but the product now has substantially more functionality than the old "CSV → Trust Score → AI explanation" roadmap anticipated.

I would not jump straight into building the ML section, though. The correct sequence is:

```
STAGE 1   Landing Page ✅
   ↓
STAGE 2   Backend Foundation
   ↓
STAGE 3   Dataset Ingestion + Profiling
   ↓
STAGE 4   Cleaning & Preparation
   ↓
STAGE 5   Deterministic Trust Engine
   ↓
STAGE 6   Analytics Workspace
   ↓
STAGE 7   ML Workspace (Regression + Classification)
   ↓
STAGE 8   AI Assistant (Gemini / Groq / Optional)
   ↓
STAGE 9   Saved Models + Prediction
   ↓
STAGE 10  Integration, Polish & Validation
```

That sequence matters. We should not build the ML UI first simply because it's exciting. The ML system depends on trustworthy ingestion, profiling, cleaning, transformation tracking, and data preparation. Likewise, AI comes after the deterministic systems it is supposed to explain.

### One recommendation I'd add

I strongly recommend that we make "Data Readiness" a concept connecting all three workspaces. Not another giant feature — just a shared status.

**Example**

- For Analytics: Analytics Readiness: 86/100
- For ML: ML Readiness: 68/100 — 3 issues should be addressed before training

This is powerful because it gives TrustLake a consistent philosophy across the entire platform. The same dataset could therefore say:

```
TRUST SCORE          82/100
ANALYTICS READINESS  91/100
ML READINESS         67/100
```

And explain why.

That makes the product feel like one coherent system, rather than three unrelated tools shoved into the same website. Most importantly, it reinforces the original idea: TrustLake isn't deciding what the user should do. It's giving them evidence about whether the data is ready for what they want to do.

And yes — this is still realistic to build for free if we are disciplined about the architecture, use open-source Python/ML tooling, keep AI optional, use Gemini/Groq selectively, and avoid infrastructure-heavy features until the hardware actually demands them.
