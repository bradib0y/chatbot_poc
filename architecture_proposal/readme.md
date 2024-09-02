# LLM-Based Chat Service Architectural Proposal

## Overview

This repository contains the architectural proposal for a custom, self-hosted LLM-based chat service.

The proposed architecture aims to create a scalable, secure, and efficient system for hosting the service, tailored to handle sensitive content while avoiding issues with censorship imposed by commercial LLM providers, like ChatGPT.

The technology choices are based on what the author is most familiar with, and they are up to debate once the existing environment and fellow engineers' experience are taken into consideration.

## Key Features

- Custom-hosted LLM service using open-source tools
- FastAPI-based server with ctransformers for efficient inference
- Azure infrastructure for hosting and scaling
- Comprehensive security measures
- Backoffice AI integration for content creation and management

## Document Structure

1. [LLM Server Implementation](1-llm-server.md)
   - Details on FastAPI and ctransformers usage
   - GGUF model file handling

2. [Hosting vs. 3rd Party Comparison](2-hosting.md)
   - Cost analysis
   - Censorship considerations
   - Customization options

3. [Infrastructure and DevOps](3-infrastructure.md)
   - Azure infrastructure setup
   - Terraform for Infrastructure as Code
   - CI/CD with Azure Pipelines
   - GPU and RAM estimations

4. [Prompt Engineering](4-prompt-engineering.md)
   - User-facing AI chatbot design
   - System prompts and file resources integration
   - Character style implementation

5. [Backoffice AI Work](5-backoffice-ai.md)
   - AI-assisted character creation
   - Text2Image AI for profile pictures
   - Conversation flow management

6. [Security Considerations](6-security.md)
   - AI-specialized aspects of security: User-facing AI security measures
   - General security considerations

7. [Web Architecture](7-web-architecture.md)
   - Backend and frontend design
   - Database and caching strategies
   - Future abstraction proxy implementation

## Getting Started

To navigate this architectural proposal:

1. Start with this README for an overview.
2. Explore each linked document for detailed information on specific aspects of the architecture.
3. Refer to the [Infrastructure and DevOps](infrastructure.md) document for setup and deployment guidelines.

## Next Steps

1. Review and finalize the architectural design
2. Set up development environment
3. Begin implementation of core components
4. Conduct security audits
5. Develop and integrate AI-assisted backoffice tools

## Contact

For any questions or clarifications regarding this architectural proposal, please contact the project lead.

---

This proposal is a living document and may be updated as the project evolves.
