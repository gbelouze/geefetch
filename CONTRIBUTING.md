# Contributing guidelines

## Contributing code

1. (optional) Set up a Python development environment
   (advice: use [venv](https://docs.python.org/3/library/venv.html),
   [virtualenv](https://virtualenv.pypa.io/), or [miniconda](https://docs.conda.io/en/latest/miniconda.html))
2. Clone the repository and install `geefetch`
   ```bash
   git clone https://github.com/gbelouze/geefetch.git
   cd geefetch
   pip install -e .
   ```
3. Start a new branch off the main branch: `git switch -c my-new-branch main`
4. Make your code changes
5. It's nice to have common formatting options. We use `black`, `isort` and `flake8`. You can use the nice `pre-commit` tool to adhere to the repository formatting guidelines. It's beautiful, it's easy and it's free, and you don't need to know any of the underlying tools.
   ```bash
   pip install pre-commit # install pre-commit
   pre-commit install   # install the hooks for the geefetch project
   # this will prevent you from committing unformatted code
   ```
   You can then use the code checking tools by hand or run them all at once with
   ```bash
   pre-commit run --all-files
   ```
6. Commit, push, and open a pull request!
   ```bash
   git add file1 file2 file3  # add the modified files
   git commit -m "Short message to explain your changes"  # commit your changes
   git push -u origin my-new-branch  # change the branch name to the one you created in step 3.
   ```
   Use the link in the output, which should look something like `https://github.com/gbelouze/geefetch/compare/my-new-branch`, and create a *pull request*.
   Someone else will review your code and merge it to the repository !
