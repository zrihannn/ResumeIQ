# Build notes

Runtime and development dependencies are defined in the backend requirement files. Keep dependency constraints aligned with the supported deployment environments.

Before changing a pinned dependency:

- Review platform and runtime compatibility, including native package availability.
- Check transitive dependencies for unnecessary or incompatible requirements.
- Run the backend test suite and frontend production build.
- Update the dependency files and related tests together.
