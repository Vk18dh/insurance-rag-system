FROM node:18-alpine

WORKDIR /app

# Install dependencies explicitly
COPY package.json package-lock.json* ./
RUN npm install

# Copy remaining source code
COPY . .

# Expose the Vite dev server port
EXPOSE 5173

# Start the Vite development server binding to 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host"]
