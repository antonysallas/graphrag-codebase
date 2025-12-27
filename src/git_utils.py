"""Git repository cloning utilities for GraphRAG pipeline."""

import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import git
from loguru import logger


class GitCloner:
    """Handles Git repository cloning with authentication support."""

    def __init__(self, workspace_dir: Path = Path("/workspace")):
        """Initialize Git cloner.

        Args:
            workspace_dir: Directory where repositories will be cloned
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Git workspace directory: {self.workspace_dir}")

    def clone_repo(
        self,
        repo_url: str,
        branch: str = "main",
        token: Optional[str] = None,
        depth: int = 1,
    ) -> Path:
        """Clone Git repository and return path to cloned directory.

        Args:
            repo_url: Git repository URL (HTTPS or SSH)
            branch: Branch to checkout (default: main)
            token: Authentication token for private repos (HTTPS only)
            depth: Clone depth for shallow clones (default: 1 for shallow)

        Returns:
            Path to cloned repository directory

        Raises:
            ValueError: If repo_url is invalid
            git.GitCommandError: If cloning fails
        """
        if not repo_url:
            raise ValueError("Repository URL cannot be empty")

        # Extract repository name from URL
        repo_name = self._extract_repo_name(repo_url)
        clone_path = self.workspace_dir / repo_name

        # Check if already cloned
        if clone_path.exists():
            logger.info(f"Repository already exists at {clone_path}")
            return self._update_existing_repo(clone_path, branch)

        # Prepare authenticated URL for HTTPS
        auth_url = self._prepare_auth_url(repo_url, token)

        # Clone repository
        logger.info(f"Cloning repository from {repo_url}")
        logger.info(f"Branch: {branch}, Depth: {depth}")

        try:
            if depth > 0:
                # Shallow clone
                git.Repo.clone_from(
                    auth_url,
                    clone_path,
                    branch=branch,
                    depth=depth,
                    single_branch=True,
                )
                logger.info(f"Shallow clone completed: {clone_path}")
            else:
                # Full clone
                git.Repo.clone_from(
                    auth_url,
                    clone_path,
                    branch=branch,
                )
                logger.info(f"Full clone completed: {clone_path}")

            return clone_path

        except git.GitCommandError as e:
            logger.error(f"Git clone failed: {e}")
            # Clean up partial clone if it exists
            if clone_path.exists():
                shutil.rmtree(clone_path)
            raise

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from Git URL.

        Args:
            repo_url: Git repository URL

        Returns:
            Repository name

        Examples:
            https://github.com/user/repo.git -> repo
            git@github.com:user/repo.git -> repo
            https://github.com/user/repo -> repo
        """
        # Handle SSH URLs (git@github.com:user/repo.git)
        if repo_url.startswith("git@"):
            path_part = repo_url.split(":")[-1]
        else:
            # Handle HTTPS URLs
            parsed = urlparse(repo_url)
            path_part = parsed.path

        # Remove leading slash and .git extension
        path_part = path_part.lstrip("/")
        if path_part.endswith(".git"):
            path_part = path_part[:-4]

        # Get last part (repo name)
        repo_name = path_part.split("/")[-1]

        if not repo_name:
            raise ValueError(f"Could not extract repository name from URL: {repo_url}")

        return repo_name

    def _prepare_auth_url(self, repo_url: str, token: Optional[str]) -> str:
        """Prepare authenticated URL for HTTPS cloning.

        Args:
            repo_url: Original repository URL
            token: Authentication token (optional)

        Returns:
            URL with token injected if applicable
        """
        # Only inject token for HTTPS URLs
        if not repo_url.startswith("https://") or not token:
            return repo_url

        # Parse URL
        parsed = urlparse(repo_url)

        # Inject token into URL
        # https://github.com/user/repo.git -> https://token@github.com/user/repo.git
        auth_url = f"https://{token}@{parsed.netloc}{parsed.path}"

        logger.debug("Using authenticated HTTPS URL")
        return auth_url

    def _update_existing_repo(self, repo_path: Path, branch: str) -> Path:
        """Update existing repository to latest commit on branch.

        Args:
            repo_path: Path to existing repository
            branch: Branch to checkout

        Returns:
            Path to repository
        """
        try:
            repo = git.Repo(repo_path)

            # Fetch latest changes
            logger.info(f"Fetching latest changes for {repo_path}")
            origin = repo.remotes.origin
            origin.fetch()

            # Checkout branch
            if branch in repo.heads:
                repo.heads[branch].checkout()
                logger.info(f"Checked out branch: {branch}")
            else:
                # Create tracking branch
                repo.create_head(branch, origin.refs[branch])
                repo.heads[branch].set_tracking_branch(origin.refs[branch])
                repo.heads[branch].checkout()
                logger.info(f"Created and checked out branch: {branch}")

            # Pull latest changes
            origin.pull(branch)
            logger.info(f"Updated to latest commit on {branch}")

            return repo_path

        except git.GitCommandError as e:
            logger.warning(f"Could not update existing repo: {e}")
            logger.info("Proceeding with existing repository state")
            return repo_path

    def clean_workspace(self):
        """Remove all cloned repositories from workspace.

        Warning: This deletes all data in the workspace directory.
        """
        if self.workspace_dir.exists():
            logger.warning(f"Cleaning workspace: {self.workspace_dir}")
            shutil.rmtree(self.workspace_dir)
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Workspace cleaned")
