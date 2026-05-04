# TradingAgents CLI Flowchart

This document outlines the step-by-step flow of the TradingAgents CLI from the moment it is triggered until the final report is generated.

```mermaid
flowchart TD
    Start([Trigger CLI: 'tradingagents' or 'python -m cli.main']) --> Welcome[Display Welcome Message & Announcements]
    
    subgraph User Configuration
        Welcome --> Q1[Step 1: Enter Ticker Symbol]
        Q1 --> Q2[Step 2: Enter Analysis Date]
        Q2 --> Q3[Step 3: Select Output Language]
        Q3 --> Q4[Step 4: Select Analysts Team]
        Q4 --> Q5[Step 5: Select Research Depth]
        Q5 --> Q6[Step 6: Select LLM Provider]
        Q6 --> Q7[Step 7: Select Thinking Agents]
        Q7 --> Q8[Step 8: Configure Provider-Specific Settings\ne.g., Reasoning Effort]
    end

    Q8 --> InitGraph[Initialize TradingAgentsGraph]

    subgraph Execution Pipeline
        InitGraph --> AnalystTeam{I. Analyst Team}
        
        AnalystTeam -->|If Selected| Market[Market Analyst]
        AnalystTeam -->|If Selected| Social[Social Analyst]
        AnalystTeam -->|If Selected| News[News Analyst]
        AnalystTeam -->|If Selected| Fund[Fundamentals Analyst]
        
        Market --> ResearchTeam
        Social --> ResearchTeam
        News --> ResearchTeam
        Fund --> ResearchTeam
        
        ResearchTeam{II. Research Team} --> Bull[Bull Researcher]
        ResearchTeam --> Bear[Bear Researcher]
        Bull <-->|Debate| Bear
        Bull --> Manager[Research Manager]
        Bear --> Manager
        
        Manager --> TradingTeam{III. Trading Team}
        TradingTeam --> Trader[Trader Agent]
        
        Trader --> RiskTeam{IV. Risk Management}
        RiskTeam --> Aggressive[Aggressive Analyst]
        RiskTeam --> Neutral[Neutral Analyst]
        RiskTeam --> Conservative[Conservative Analyst]
        
        Aggressive --> Portfolio[V. Portfolio Management]
        Neutral --> Portfolio
        Conservative --> Portfolio
        
        Portfolio --> PortfolioManager[Portfolio Manager]
    end

    PortfolioManager --> Display[Display Complete Report in CLI]
    Display --> Save[Save Report to Disk]
    Save --> End([End])
```

## Description of Stages

1. **User Configuration**: The CLI prompts the user for various parameters required for the analysis, such as the target stock ticker, the date of analysis, the LLM provider to use, and which specific analyst agents to include.
2. **Execution Pipeline**: The core logic powered by `TradingAgentsGraph` runs. It follows a sequential flow where the output of one team feeds into the next.
   - **Analyst Team**: Gathers raw data and generates initial reports based on the selected agents.
   - **Research Team**: Engages in a debate between bullish and bearish perspectives, finalized by the Research Manager.
   - **Trading Team**: The Trader formulates an investment plan based on the research.
   - **Risk Management**: Evaluates the trader's plan from different risk perspectives.
   - **Portfolio Management**: Makes the final decision to approve or reject the trade.
3. **Output**: The final comprehensive report is displayed in the terminal and saved to the local disk in organized markdown files.
