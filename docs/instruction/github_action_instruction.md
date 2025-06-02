# GitHub Action Instruction

This document explains the principles behind GitHub Actions, how it works with GitHub Pages, and how to choose and use actions via the `uses` keyword.

---

## 🚀 What is GitHub Actions?

GitHub Actions is an **event-driven CI/CD (Continuous Integration and Continuous Deployment) system** provided by GitHub. It allows you to automate tasks like building, testing, and deploying your code when events (e.g., `push`, `pull_request`) occur in your repository.

---

## 🔧 Key Concepts

### 1. Workflow
A YAML file that defines automation logic.

### 2. Events (`on`)
Trigger conditions like `push`, `pull_request`, `release`, etc.

### 3. Jobs
A job runs in a separate VM and contains multiple steps.

### 4. Steps
Each task in a job. It can either run a shell command or use a prebuilt action.

---

## 🌐 GitHub Pages Deployment with GitHub Actions

You can use GitHub Actions to automatically deploy static sites (e.g., React, Vite, Hugo, Docusaurus) to GitHub Pages.

### ✅ Sample Workflow: Deploy React App

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout source code
      uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'

    - name: Install dependencies
      run: npm install

    - name: Build site
      run: npm run build

    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./build
```

### 🔁 Process Summary

```text
[Push to main]
      ↓
[GitHub Action Triggered]
      ↓
[Site is Built using npm/yarn]
      ↓
[Output deployed to gh-pages branch]
      ↓
[GitHub Pages serves from gh-pages branch]
```

### 📌 Where to Configure GitHub Pages

1. Go to your repo: `Settings > Pages`
2. Set Source to `Deploy from a GitHub Actions workflow`

---

## ✅ Use Cases for GitHub Pages + Actions

- React/Vite-based sites
- Static documentation (e.g., Docusaurus, MkDocs)
- Project portfolios
- Interactive LLM UI prototypes

---

## 🧩 What is `uses`?

In the `steps` section, `uses` is a keyword to **invoke an existing GitHub Action**.

### Syntax
```yaml
uses: <owner>/<repo>@<version>
```

| Component     | Description                           |
|---------------|---------------------------------------|
| `<owner>`     | The GitHub user or organization       |
| `<repo>`      | The repository name containing the action |
| `<version>`   | Version tag like `v1`, `v2`, or SHA   |

---

## 📦 How to Decide Which Action to Use

1. **Know Your Task**  
   - Clone repo → `actions/checkout`  
   - Set Node version → `actions/setup-node`  
   - Deploy to GitHub Pages → `peaceiris/actions-gh-pages`  
   - Upload to GitHub Releases → `softprops/action-gh-release`

2. **Use GitHub Marketplace**  
   - Visit: [GitHub Marketplace - Actions](https://github.com/marketplace?type=actions)  
   - Search by task like "deploy", "docker", "upload", etc.

3. **Best Practices**
   - Choose actions with good documentation, recent maintenance, and high star counts.

---

## 🧪 Example: `uses` vs `run`

```yaml
steps:
  - name: Use official action
    uses: actions/checkout@v4

  - name: Do the same manually
    run: git clone https://github.com/${{ github.repository }}
```

`uses` is safer and more standardized—it's recommended over writing raw commands.

---

## 📝 Final Notes

- Use `uses` for reusable, clean automation.
- Always check documentation and license of third-party actions.
- Use secrets (`${{ secrets.X }}`) to securely manage API keys, tokens, etc.