# GitHub Development Workflow Guide

This document outlines a typical GitHub development workflow for collaborative projects. It covers switching to the development branch, making changes, pushing commits, creating pull requests (PRs), merging, and leveraging GitHub Actions.

---

## 1. Clone the Repository

If you haven't already, clone the repository to your local machine:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

---

## 2. Switch to the Development Branch

Most teams use a `dev` or `develop` branch for ongoing work. Switch to it:

```bash
git checkout dev
```

If you don't have the latest changes:

```bash
git pull origin dev
```

---

## 3. Create a Feature or Bugfix Branch

Create a new branch for your work to keep changes isolated:

```bash
git checkout -b feature/your-feature-name
# or for bugfixes
git checkout -b bugfix/your-bug-description
```

---

## 4. Make Changes and Commit

Edit, add, or delete files as needed. Then stage and commit your changes:

```bash
git add .
git commit -m "Add feature: your feature description"
```

---

## 5. Push Your Branch to GitHub

Push your new branch to the remote repository:

```bash
git push origin feature/your-feature-name
```

---

## 6. Create a Pull Request (PR)

1. Go to your repository on GitHub.
2. You'll see a prompt to create a pull request for your recently pushed branch. Click **Compare & pull request**.
3. Fill in the PR title and description. Make sure the base branch is `dev` and the compare branch is your feature/bugfix branch.
4. Submit the pull request.

---

## 7. Code Review & CI/CD (GitHub Actions)

- Team members review your PR and may request changes.
- GitHub Actions (if configured) will automatically run tests and checks on your PR.
- Address any feedback or failing checks by pushing more commits to your branch.

---

## 8. Merge the Pull Request

Once approved and all checks pass:

1. Click **Merge pull request** on GitHub.
2. Delete your feature/bugfix branch if prompted.

---

## 9. Sync Your Local Repository

After merging, update your local `dev` branch:

```bash
git checkout dev
git pull origin dev
```

---

## 10. (Optional) Production Release

- When ready, create a PR from `dev` to `main` (or `master`) for production deployment.
- Follow the same review and merge process.

---

## 11. GitHub Actions Overview

- **GitHub Actions** automate workflows like testing, linting, and deployment.
- Actions run on PRs, pushes, or merges, as defined in `.github/workflows/`.
- Check the **Actions** tab on GitHub for workflow status and logs.

---

## Best Practices

- Commit small, focused changes.
- Write clear PR titles and descriptions.
- Review and test code before merging.
- Keep branches up to date with `dev` to avoid conflicts.

---

Happy coding! 