# Quarry.io Gherkin Samples

Feature: Full-text search
  Scenario: Find a booking by keyword
    Given I have 500 screenshots indexed
    And at least one contains the text "PNR X7K9Q"
    When I search for "X7K9Q"
    Then I should see that screenshot in the top 3 results
    And the matching text is highlighted on the image detail view

Feature: Smart actions for dates
  Scenario: Create a calendar event from a date entity
    Given a screenshot contains "Meeting on 22 Nov 2025 at 3:30 PM"
    When I open the screenshot
    Then I should see a suggested action "Add to Calendar"
    And tapping it should prefill an event on 22 Nov 2025 15:30
    And I can confirm to save the event

Feature: Persistent dynamic album
  Scenario: Save search as Smart Album
    Given I search "receipt" and filter by Amount > $10
    When I save it as "Receipts $10+"
    And I later add a new qualifying screenshot
    Then it should automatically appear in "Receipts $10+"

Feature: Local RAG Q&A
  Scenario: Answer with source image links (offline)
    Given I have indexed screenshots with a booking reference "ABC123"
    And offline-only mode is enabled
    When I ask "What is my latest booking reference?"
    Then I receive "ABC123" as the answer
    And at least one citation is shown
    And tapping the citation opens the source image with highlight

Feature: Secure Sync onboarding
  Scenario: Enabling encrypted sync
    Given I am on Settings > Sync
    When I enable "Secure Sync"
    Then I am shown a recovery phrase of 24 words
    And the app confirms keys are created on-device
    And subsequent uploads are encrypted end-to-end


