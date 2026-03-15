# Five FDE Day-One Answers

## 1. What is the primary data ingestion path?
Data enters the system via external Telegram APIs, is serialized to JSON, and loaded into a PostgreSQL raw schema.
*   **Scraping:** `scripts\data_scraping.py` asynchronously retrieves messages and media from pharmaceutical/health channels.
*   **Storage:** Messages are stored as structured JSON with metadata (sender, timestamp, views).
*   **Loading:** `scripts\load_raw_data.py` ingests these JSON files into the Postgres `raw.telegrammessages` table defined in `telegram_data\models\staging\sources.yml`.
*   **Orchestration:** `telegram_pipeline\pipelines\telegram_pipeline.py` schedules this end-to-end flow daily.

## 2. What are the 3-5 most critical output datasets/endpoints?
The system delivers value through three FastAPI endpoints and two core analytical mart tables.
*   **API Endpoints:** `api\main.py` exposes REST services for **channel activity analytics**, **message search**, and **product popularity reporting** (keyword counts).
*   **Fact Tables:** `telegram_data\models\marts\core\fct_messages.sql` aggregates message volume and engagement metrics; `telegram_data\models\marts\core\fct_image_detections.sql` aggregates object detection results (pill classification) linked to messages.
*   **Dimension Tables:** `telegram_data\models\marts\core\dim_channels.sql` and `dim_dates.sql` provide standardized lookup keys for reporting.

## 3. What is the blast radius if the most critical module fails?
Failure of **`api\database.py`** (Architectural Hub) would immediately brick the entire serving layer.
*   **Direct Impact:** This module configures the SQLAlchemy engine and `SessionLocal` factory. It is imported by `api\crud.py`, `api\models.py`, and `api\main.py`.
*   **Downstream Breakage:** All three REST endpoints (`/channel_activity`, `/search`, `/product_popularity`) would fail to initialize or query data.
*   **Secondary Risk:** Failure of `telegram_pipeline\pipelines\telegram_pipeline.py` would halt daily data ingestion, starving the API of fresh records and stopping downstream dbt transformations (`fct_messages`).

## 4. Where is the business logic concentrated vs. distributed?
Business logic is **distributed** across Python (ingestion/serving), SQL (transformation), and Configuration (ML).
*   **Python (Ingestion & Serving):** `scripts\data_scraping.py` handles scraping logic; `api\crud.py` contains analytics logic (trends, keyword search); `scripts\image_detection.py` handles CV inference.
*   **SQL (Transformation):** `telegram_data\models\marts\core\fct_messages.sql` and `stg_telegram_messages.sql` encode data cleaning, standardization, and aggregation logic within dbt models.
*   **Configuration (ML):** `runs\detect\train7\args.yaml` concentrates hyperparameter logic for the YOLOv8 pill detection model (batch size, epochs, augmentation).

## 5. What has changed most frequently in the last 90 days?
**No files show recorded changes** in the provided analysis window.
*   **Evidence:** The **Hotspots** list explicitly reports `0 commits` for all key files, including `docker-compose.yml`, `api\main.py`, `scripts\data_scraping.py`, and `telegram_pipeline\pipelines\telegram_pipeline.py`.
*   **Implication:** This indicates the repository is either a fresh initialization, a static snapshot for analysis, or velocity tracking is not enabled for this view. There is no churn data to prioritize refactoring based on frequency.