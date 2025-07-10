# Use a slim Python image for smaller size
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any (none explicitly needed for basic python/sqlite-utils)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     sqlite3 \ # Not strictly needed if sqlite-utils handles it
#     && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Don't store cache locally, reduces image size
# --compile: Compile Python source files into bytecode, improves startup time
RUN pip install --no-cache-dir --compile -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your Slack bot listens on
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:3000/ || exit 1

# Set environment variables
# These can also be set at runtime using -e flag with docker run

#-----ENV GITHUB_TOKEN=${GITHUB_TOKEN}
#-----ENV SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
#-----ENV SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
#-----ENV GITHUB_OWNER=${GITHUB_OWNER}
#-----ENV GITHUB_REPO=${GITHUB_REPO}
#-----ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
#-----ENV OPENROUTER_API_BASE=${OPENROUTER_API_BASE}
#-----ENV OPENROUTER_MODEL_NAME=${OPENROUTER_MODEL_NAME}
#-----ENV REPORT_AUTHOR_NAME=${REPORT_AUTHOR_NAME}
#-----ENV REPORT_AUTHOR_POSITION=${REPORT_AUTHOR_POSITION}
# Copy the .env file to the container
#-------------COPY .env .env
# Ensure the .env file is readable by the application
#-----------RUN chmod 644 .env
# Set the working directory to where your main application file is located
#----------WORKDIR /app/bot
# Ensure the main.py file is executable
#------RUN chmod +x main.py    
# Install any additional Python packages needed for your application
#--------RUN pip install --no-cache-dir -r requirements.txt
# Set the entrypoint to run your application
# This assumes main.py is the entry point of your application

# If you have a different entry point, adjust accordingly
#------ENTRYPOINT ["python", "main.py"]
# Set the default command to run when the container starts
# This can be overridden by passing a different command when running the container
# If you want to run a different command, you can do so by passing it when running the container
# For example, you can run the container with:
# docker run -e GITHUB_TOKEN=your_token -e SLACK_BOT_TOKEN=your_token -e SLACK_SIGNING_SECRET=your_secret \
#   -e GITHUB_OWNER=your_owner -e GITHUB_REPO=your_repo \
#   -e OPENROUTER_API_KEY=your_key -e OPENROUTER_API_BASE=your_base \
#   -e OPENROUTER_MODEL_NAME=your_model_name -e REPORT_AUTHOR_NAME=your_name \
#   -e REPORT_AUTHOR_POSITION=your_position \   
#   your_image_name python main.py
# If you want to run the bot with a different command, you can do so by passing


# Command to run your application
# main.py handles loading .env, seeding, and starting the bot
CMD ["python", "main.py"]