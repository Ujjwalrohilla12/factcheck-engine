# FactCheck AI - Deployment Guide

Complete guide for deploying FactCheck AI to various platforms.

## Table of Contents
1. [Local Deployment](#local-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Streamlit Cloud](#streamlit-cloud)
4. [AWS Deployment](#aws-deployment)
5. [Heroku Deployment](#heroku-deployment)

---

## Local Deployment

### Quick Start (5 minutes)

1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/factcheck-ai.git
   cd factcheck-ai
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   nano .env
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Access at:** http://localhost:8501

---

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Ensure Docker is installed:**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Create .env file:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Access at:** http://localhost:8501

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Manual Docker Build

```bash
# Build image
docker build -t factcheck-ai:latest .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-... \
  -e TAVILY_API_KEY=tvly-... \
  -v $(pwd)/output:/app/output \
  factcheck-ai:latest
```

---

## Streamlit Cloud (Recommended for Production)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at https://share.streamlit.io)

### Deployment Steps

1. **Push code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Visit Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Click "New app"

3. **Configure deployment:**
   - **Repository:** Select your factcheck-ai repo
   - **Branch:** main
   - **Main file path:** app.py

4. **Add secrets:**
   - Click "Advanced settings" → "Secrets"
   - Add your API keys in TOML format:
   ```toml
   OPENAI_API_KEY = "sk-your-key-here"
   TAVILY_API_KEY = "tvly-your-key-here"
   LLM_MODEL = "gpt-4o-mini"
   ```

5. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes for deployment
   - Your app is now live!

### Monitoring
- View logs in the Streamlit Cloud dashboard
- Monitor app performance and usage
- Update code by pushing to GitHub (auto-deploys)

---

## AWS Deployment

### Option 1: EC2 + Streamlit Cloud

1. Create an EC2 instance (t3.medium or larger)
2. Install Python, pip, git
3. Clone the repository and follow local deployment steps
4. Use systemd to run the app as a service

### Option 2: AWS Lambda + API Gateway

1. Package the app as a Lambda function
2. Use AWS API Gateway for HTTP endpoints
3. Store API keys in AWS Secrets Manager

### Option 3: ECS + Fargate

1. Push Docker image to Amazon ECR:
   ```bash
   aws ecr create-repository --repository-name factcheck-ai
   docker tag factcheck-ai:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/factcheck-ai:latest
   aws ecr get-login-password | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/factcheck-ai:latest
   ```

2. Create ECS task definition
3. Deploy to Fargate cluster
4. Configure Application Load Balancer

---

## Heroku Deployment

### Prerequisites
- Heroku account (free tier available)
- Heroku CLI installed

### Deployment Steps

1. **Create Procfile:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Initialize Heroku:**
   ```bash
   heroku login
   heroku create factcheck-ai
   ```

3. **Add buildpacks:**
   ```bash
   heroku buildpacks:add heroku/python
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set OPENAI_API_KEY=sk-...
   heroku config:set TAVILY_API_KEY=tvly-...
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

6. **View logs:**
   ```bash
   heroku logs --tail
   ```

---

## Production Checklist

- [ ] API keys stored in environment variables
- [ ] File upload size limits enforced
- [ ] Error logging configured
- [ ] Rate limiting implemented
- [ ] CORS properly configured
- [ ] HTTPS enabled (automatic on cloud platforms)
- [ ] Database backups scheduled
- [ ] Monitoring and alerts set up
- [ ] Documentation updated
- [ ] Load testing completed

---

## Performance Optimization for Production

1. **Enable Streamlit Caching:**
   ```python
   @st.cache_data
   def cached_extraction(text):
       return extract_claims(text)
   ```

2. **Implement Request Batching:**
   - Process multiple claims in parallel
   - Use asyncio for I/O operations

3. **Database Integration:**
   - Store results in PostgreSQL
   - Implement caching layer with Redis

4. **CDN Setup:**
   - Serve static assets via CloudFront (AWS)
   - Enable gzip compression

5. **Monitoring:**
   - Set up Datadog, New Relic, or CloudWatch
   - Monitor API usage and costs
   - Alert on errors and performance issues

---

## Scaling Strategies

### Horizontal Scaling
- Use load balancer (AWS ALB, Nginx)
- Run multiple instances behind the balancer
- Share API rate limits across instances

### Vertical Scaling
- Upgrade instance type
- Increase memory and CPU
- Optimize code for performance

### Queue-Based Processing
- Use Celery + Redis for async task processing
- Handle long-running verifications asynchronously
- Implement webhooks for result notifications

---

## Cost Estimation

### Free Tier (Development)
- Streamlit Cloud: Free
- OpenAI API: Pay-as-you-go (~$0.01-0.05 per claim)
- Tavily Search: Free plan available
- **Monthly estimate:** $0-10

### Production Tier (Small)
- Streamlit Cloud: ~$7/month
- OpenAI API: ~$50-100/month (1000 claims)
- Tavily Search: $10-50/month
- AWS/Database: ~$20-50/month
- **Monthly estimate:** $100-200

### Enterprise Tier (Large)
- Dedicated servers: $100-500/month
- API costs: $500-2000/month
- Support and monitoring: $100-500/month
- **Monthly estimate:** $700-3000+

---

## Troubleshooting Deployment Issues

### Port Already in Use
```bash
# Find and kill process
lsof -i :8501
kill -9 <PID>
```

### API Key Not Found
- Verify `.env` file exists
- Check `OPENAI_API_KEY` and `TAVILY_API_KEY`
- Test locally before deploying

### Docker Build Fails
```bash
# Clear Docker cache
docker system prune -a
# Rebuild
docker-compose up --build
```

### Out of Memory
- Reduce claim chunk size in `claim_extractor.py`
- Implement pagination for large documents
- Use database for persistent storage

---

## Support and Maintenance

- Regular dependency updates: `pip list --outdated`
- Monitor API rate limits
- Review logs for errors
- Update documentation
- Test new features in staging first

---

For detailed setup instructions, see [README.md](README.md)
