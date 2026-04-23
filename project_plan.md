# Text-Based Adventure Game Engine - Detailed Project Plan

## 1. Project Overview
This project involves developing a robust and extensible Text-Based Adventure Game Engine that combines a powerful runtime system with integrated authoring tools. The goal is to provide a unified platform capable of supporting interactive storytelling, complex dynamic worlds, and user-friendly world-building within a 10-week development period.

## 2. Technical Stack & Tools
- **Programming Language**: Python, Java, C++, or C# (based on team agreement).
- **Architecture**: Object-Oriented Design (OOD) strictly utilizing OOP principles like inheritance, encapsulation, polymorphism, and aggregation.
- **Documentation & Modeling**: Mermaid for UML diagrams, Microsoft Office / Google Workspace tools.
- **Version Control**: GitHub for source code hosting, documentation, and issue management.
- **AI Assistance**: GPTs for GenAI-assisted development to accelerate tasks across all phases.

## 3. Core Engine Concepts & Architecture
### 3.1. Game World Structure
- **Entity Model**: An abstract `Entity` class that handles shared logic for `Player` and `NPC` through inheritance.
- **Environment**: Interconnected `Room` objects that utilize composition/aggregation to hold `Item` objects.
- **State Management**: Real-time tracking of player progress, inventory, room states, NPC dialogues, and conditional logic.

### 3.2. Core Runtime Mechanisms
- **Command Parser**: Robust interpretation of natural language inputs (e.g., "go north", "take sword") executing actions via the **Command Pattern**.
- **Event & Trigger System**: Leverages the **Observer Pattern** to manage asynchronous game events like dynamic combat, unlocking areas, and triggering dialogue.
- **Game State Persistence**: Implements Save/Load functionalities using **JSON serialization** to prevent data loss.

### 3.3. Authoring Tool (Game Editor)
- Specific tools focusing on empowering content creators to structure rooms, instantiate items, place NPCs, and script dialogues.
- Integration of the **Factory Pattern** for rapidly building and deploying in-game assets within the editor.

---

## 4. Deliverables Roadmap

The following deliverables map directly to the course project guidelines:

### Deliverable 1: Software Requirements Specification (SRS) & Use Cases
- Fully document the functional and non-functional requirements for the Engine Prototype and Game Editor.
- Identify our core user stories and actor requirements.
- **Example Use Cases to Document**:
  - *Player*: Move to Room, Inspect Environment, Save Current Progress.
  - *Designer*: Create New Item, Map Room Connection, Edit NPC Dialogue.

### Deliverable 2: Software Design Document (SDD)
- Produce a detailed technical breakdown mapping out the Object-Oriented foundations.
- Embed critical architecture diagrams generated via Mermaid (Class Diagrams, Sequence Diagrams, State Machines).
- Clearly define where and how assigned Design Patterns (Command, Factory, Observer) govern internal systems.

### Deliverable 3: Source Code and Executables
- Implement the functional prototype highlighting core gameplay mechanics, a CLI engine, and world-building capabilities.
- Ensure the codebase boasts rigorous encapsulation and extensively tests polymorphism.
- Deliver all files via GitHub alongside execution instructions.

### Deliverable 4: Test Procedures
- Create systematic guidelines mapping out happy-path, alternative, and negative evaluation scenarios.
- Highlight specific areas prone to error, such as the command parser dealing with unexpected inputs or edge-cases in JSON serialization/deserialization.

### Deliverable 5: Test Reports
- A comprehensive execution log demonstrating the outcomes of the defined Test Procedures.
- Coverage metrics highlighting how successfully bugs were isolated, validated, and mitigated before final submission.

### Deliverable 6: GenAI Prompts
- An ongoing record of all major Generative AI prompts created throughout the lifecycle.
- This effectively tracks how much tools like ChatGPT were leveraged for brainstorming requirements, refining class structures, or debugging failing test cases.

## 5. Proposed Timeline / Milestones (10 Weeks)
- **Weeks 1-2**: Team formation, establishing Git repository, requirements elicitation, finalizing **SRS Deliverable**.
- **Weeks 3-4**: Architecture charting, establishing OOP class hierarchies, drafting and finalizing the **SDD Deliverable**.
- **Weeks 5-7**: Core engine implementation focusing on the Command Parser, standard action sets, and terminal interface.
- **Weeks 8-9**: Finalizing JSON Serialization, integrating Editor authoring tools, and robust refactoring.
- **Week 10**: Generating **Test Procedures & Reports**, consolidating **GenAI prompts**, creating presentation, and project handover.
