# Apple Yield Estimator with YOLOv8

A computer vision system for detecting and counting apples in orchard images using YOLOv8s and ONNX Runtime. This FastAPI-based application provides real-time apple detection, health classification, and yield estimation capabilities.

## Features

- 🍎 **Apple Detection**: Detects healthy and damaged apples using YOLOv8s model
- 📊 **Yield Estimation**: Calculates total apple count and health index
- 🖼️ **Image Processing**: Handles JPEG/PNG image uploads for analysis
- 🗄️ **Database Storage**: PostgreSQL integration for storing estimation records
- 🐳 **Docker Support**: Containerized deployment with Docker Compose
- 🚀 **FastAPI Backend**: High-performance async API framework

## Model Information

- **Architecture**: YOLOv8s (small variant)
- **Format**: ONNX (optimized for inference)
- **Classes**: 
  - `apple` (healthy apples)
  - `damaged_apple` (damaged/defective apples)
- **Input Size**: 640x640 pixels
- **Model Location**: `app/models/weights/best_model.onnx`

## Project Structure

```
yieldEstimator/
├── app/
│   ├── api/endpoints/
│   │   ├── estimator.py      # Main estimation endpoint
│   │   └── history.py        # Historical data endpoint
│   ├── db/
│   │   ├── models.py         # SQLAlchemy database models
│   │   └── session.py        # Database session configuration
│   ├── models/
│   │   ├── inference.py      # YOLOv8 inference engine
│   │   └── weights/
│   │       └── best_model.onnx # Trained model weights
│   ├── schemas/
│   │   └── yield_schema.py   # Pydantic response schemas
│   └── main.py               # FastAPI application entry point
├── docker-compose.yml        # Docker orchestration
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
└── .env                    # Environment variables
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- PostgreSQL (if running locally without Docker)

### Installation with Docker

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd yieldEstimator
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Build and start services:**
   ```bash
   docker compose up --build -d
   ```

4. **Verify deployment:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5432

### Local Development

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL:**
   ```bash
   docker compose up db -d
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Apple Detection & Yield Estimation

**Endpoint:** `POST /api/estimator/estimate`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/estimator/estimate" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_apple_image.jpg"
```

**Response:**
```json
{
  "id": 1,
  "filename": "uuid_your_image.jpg",
  "healthy_count": 15,
  "damaged_count": 3,
  "total_count": 18,
  "health_index": 83.33,
  "created_at": "2024-01-01T12:00:00"
}
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Model Inference Details

The inference engine (`app/models/inference.py`) performs:

1. **Preprocessing:**
   - Image resizing to 640x640
   - BGR to RGB conversion
   - Normalization to [0,1] range
   - Dimension reordering (HWC → CHW)

2. **Detection:**
   - ONNX Runtime inference with CPU execution
   - Confidence threshold: 0.4
   - Non-Maximum Suppression (NMS) threshold: 0.45

3. **Post-processing:**
   - Bounding box filtering
   - Class classification (healthy vs damaged)
   - Count aggregation and health index calculation

## Database Schema

The application stores estimation records in PostgreSQL with the following schema:

```sql
CREATE TABLE yield_records (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    healthy_count INTEGER NOT NULL,
    damaged_count INTEGER NOT NULL,
    total_count INTEGER NOT NULL,
    health_index FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables (.env)

```env
# Database Configuration
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=apple_yield_db
POSTGRES_HOST=localhost

# Application Settings
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
```

## Performance Considerations

- **Model**: YOLOv8s optimized for balance between speed and accuracy
- **Inference**: ONNX Runtime with CPU provider (suitable for cloud deployment)
- **Image Processing**: OpenCV for efficient computer vision operations
- **API**: FastAPI with async support for concurrent requests

## Monitoring and Logging

- Application logs available in Docker container logs
- Health check endpoint for monitoring service status
- Database connection retry logic for robust deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL container is running
   - Verify environment variables in .env file
   - Check network connectivity between containers

2. **Model Loading Error**
   - Verify `best_model.onnx` exists in `app/models/weights/`
   - Check file permissions and accessibility

3. **Memory Issues**
   - Monitor container resource usage
   - Adjust Docker memory limits if needed
   - Consider optimizing batch processing for large images

### Docker Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild without cache
docker compose build --no-cache

# Access database
docker compose exec db psql -U your_username -d apple_yield_db
```