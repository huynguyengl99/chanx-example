# Chanx Example

Full examples for chanx package usability

## Stack & Framework

- [Django](https://www.djangoproject.com/) - Batteries-included Python web framework
- [Django REST Framework](https://www.django-rest-framework.org/) - Powerful toolkit for building Web APIs
- [PostgreSQL](https://www.postgresql.org/) - Well-known open source database system
- [Redis](https://redis.io/) - In-memory data structure store and more.

## Prerequisites

Before starting development, ensure you have the following installed:

- [UV](https://docs.astral.sh/uv/): Python version & package management
- [Docker](https://www.docker.com/products/docker-desktop/): Docker app for launching services like db, redis, etc.

## Getting Started

### Environment & Dependencies Setup

Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate
```

Install all dependencies:
```bash
uv sync
```

### Running the Application

1. **Configure environment variables**: Edit the [.env](.env) file with your settings.

2. **Start Docker services**:
```bash
docker compose up --detach
```

3. **Run database migrations**:
```bash
scripts/manage.sh migrate
```

4. **Create a superuser** (to access admin page):
```bash
scripts/manage.sh createsuperuser
```

5. **Start the development server**:
```bash
scripts/manage.sh runserver 8000
```

6. **Access the API**:
   - API playground (Swagger): http://localhost:8000/api/schema/swg/
   - API documentation: http://localhost:8000/api/schema/redoc/
   - Admin interface: http://localhost:8000/admin/

### Setting Up Pre-commit Hooks (Optional)

To automatically format code and check dependencies before commits:
```bash
pre-commit install
```

## Development Tools

### Useful Commands

The [scripts/manage.sh](scripts/manage.sh) script provides convenient aliases for Django management commands:

- `scripts/manage.sh runserver 8000` - Run local development server
- `scripts/manage.sh createsuperuser` - Create superuser for admin access
- `scripts/manage.sh shell_plus` - Interactive shell with models pre-loaded
- `scripts/manage.sh makemigrations` - Create new database migrations
- `scripts/manage.sh migrate` - Apply database migrations

For a full list of available commands, see:
- [Django official commands](https://docs.djangoproject.com/en/4.2/ref/django-admin/)
- [Django Extensions commands](https://django-extensions.readthedocs.io/en/latest/command_extensions.html)

### Package Management

We use [UV](https://docs.astral.sh/uv/) for dependency management:

- **Add a dependency**: `uv add package_name`
- **Add a dev dependency**: `uv add --dev package_name`
- **Update dependencies**: `uv sync`

### Code Quality

We maintain code quality using:

- **[Ruff](https://pypi.org/project/ruff/)** - Fast Python linter and formatter
- **[Black](https://github.com/psf/black)** - Code formatting
- **[mypy](https://mypy.readthedocs.io/)** - Static type checking with Django plugins
- **[Pyright](https://github.com/microsoft/pyright)** - Advanced static type checker
- **[toml-sort](https://github.com/pappasam/toml-sort)** - TOML file formatting

These tools are wrapped in the [scripts/lint.sh](scripts/lint.sh) script:
- **Lint only**: `scripts/lint.sh`
- **Auto-format**: `scripts/lint.sh --fix`

### Type Checking

We use dual type checking for maximum safety and comprehensive coverage:

```bash
# Run mypy on the main project
scripts/mypy.sh

# Run pyright for additional static analysis
pyright
```

Both type checkers provide different advantages:
- **mypy**: Specifically configured for Django with dedicated plugins for Django and DRF
- **pyright**: Microsoft's fast type checker with advanced inference capabilities

Configuration files:
- mypy: [mypy.ini](mypy.ini) (with Django and DRF plugins configured)
- pyright: [pyproject.toml](pyproject.toml) or [pyrightconfig.json](pyrightconfig.json)

### Commit Guidelines

We use [Commitizen](https://commitizen-tools.github.io/commitizen/) for consistent commit messages:

```bash
# Create a commit using commitizen
cz commit
```

This ensures commits follow the [Conventional Commits](https://www.conventionalcommits.org/) format:
- `feat`: new features
- `fix`: bug fixes
- `docs`: documentation updates
- `refactor`: code improvements
- `test`: testing changes

### Pre-commit Hooks

Pre-commit hooks run automatically on each commit to ensure code quality:

1. **Install hooks**: `pre-commit install`
2. **Run manually**: `pre-commit run --all-files`

Configuration is in [.pre-commit-config.yaml](.pre-commit-config.yaml).

## Testing

### Running Tests

```bash
# Run all tests
pytest chanx_example

# Run with coverage
pytest --cov-report term-missing --cov=chanx_example chanx_example

# Run specific test file
pytest chanx_example/tests/test_example.py
```

### Using Tox for Complete Testing

For testing across multiple Python versions:

```bash
# Install tox
uv tool install tox

# Run tests on all Python versions
tox

# Run tests for specific environment
tox -e py311

# Run linting checks
tox -e lint

# Generate coverage report
tox -e coverage
```

## Development Best Practices

- **Keep changes focused**: Each PR should address a single concern
- **Write tests**: Include tests for all new functionality
- **Add type annotations**: All code should be properly typed
- **Follow Django conventions**: Use Django best practices for models and views
- **Document your code**: Add docstrings to all public functions and classes
