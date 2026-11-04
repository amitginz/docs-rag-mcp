# Git workflow

## Branches and pull requests
Work on a short-lived feature branch created from the main branch. Open a pull request so teammates can review the change and so CI can run the tests before merging. Keep pull requests small and focused on one change.

## Commits
Write commit messages in the imperative mood, for example "Add retry to the payment client". The first line summarizes the change in about 50 characters; the body explains why.

## Rebase and merge
`git rebase main` replays your commits on top of the latest main branch for a linear history. Never rebase commits that others have already pulled. A merge commit preserves the exact branch history instead.

## Undoing changes
`git revert` creates a new commit that undoes an earlier one and is safe on shared branches. `git reset --hard` discards local changes and rewrites history, so use it only on your own unpublished work.
