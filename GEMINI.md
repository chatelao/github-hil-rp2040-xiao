# Goal

Alle nötigen Skripte um auf einem XIAO-RP2040 Board ein Firmware aus einem Github Action Flow zu installieren.

# Structure
- `CONCEPT.md`: The overall structure of the product, including Business & Use Cases as well as the High-Level Architecture.
- `DESIGN.md`: The detailed design of the solution, including the architecture, used tech stack for development, production and testing, etc.
- `TOP_ARCHITECTURE.puml`: The top-level component overview showing all major modules and the dataflows between them.
- `ROADMAP.md`: The list of accomplished and planned steps of the project.
- `TECHNICAL_DEBTS.md`: If you find technical debts, like outdate components, security flaws, old patterns, etc. log them here, but don’t fix them until asked to do so.
- `README.md`: Add a link to the GitHub pages if any are produced / present.
- `/specification/`: External Know-How as datasheet, standards, etc. Should be converted to Markdown if PDF, etc.
- `/src/`: The source code of the project
- `/test/`: All tools, configurations & test cases
- `/build/`: Only temporary place for compilation, may be cached by Github

# `CONCEPT.md` handling
- The `CONCEPT.md` add the business and use cases to the top Goal this file.
- It contains an architecture with top-level functional components and their business interfaces.
- It does not contain all precise implementation choices.
- Every major choice is first drawn out as three alternatives, the best one is chosen and the ohter, discarded ones kept in summary in the last chapter of the concept.

# `DESIGN.md`: 
- The `DESIGN.md` derives all necessary technological choices from `CONCEPT.md`.
- It does contain precise implementation choices.
- Every major choice is first drawn out as three alternatives, the best one is chosen and the ohter, discarded ones kept in summary in the last chapter of the concept.
- It contains a detailed architecture of all components and their technical interfaces.
- Included the TOP_ARCHITECTURE.puml` as dynamic-rendering image as soon as available.

## REST-API
- If the API is used, always regenerate the client SDKs and the server stubs from the original interface definitions
- If there are OpenAPI definitions, render them with redocly to the GH page directory /apis.
- If there are othe API definitions, render them with suitable tools to the GH page directory /apis too.
- Verify and add descriptions to the API definitions until they are useable for any product manager / developer using them later.
- If there are REST-APIs, describe them in `api/openapi.yaml`
- If there are SOAP-APIs, describe them in `api/api.wsdl`
- Keep the api definitions up-to-date with every system change

## Command-Line Interface (CLI)
- Every option should be available as short and long form
