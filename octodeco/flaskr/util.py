import git;

try:
    _repo = git.Repo(search_parent_directories=True);
    CURRENT_GIT_COMMIT = _repo.head.object.hexsha;
    CURRENT_GIT_BRANCH = _repo.active_branch;
except:
    CURRENT_GIT_COMMIT = 'N/A';
    CURRENT_GIT_BRANCH = 'N/A';

