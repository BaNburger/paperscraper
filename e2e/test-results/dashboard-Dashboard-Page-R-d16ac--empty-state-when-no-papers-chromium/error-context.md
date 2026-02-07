# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]:
    - img [ref=e7]
    - heading "Create an account" [level=3] [ref=e10]
    - paragraph [ref=e11]: Get started with Paper Scraper
  - generic [ref=e12]:
    - generic [ref=e13]:
      - generic [ref=e14]: 5 per 1 minute
      - generic [ref=e15]:
        - text: Full Name
        - textbox "Full Name" [ref=e17]:
          - /placeholder: John Doe
          - text: Test User 1770435239308
      - generic [ref=e18]:
        - text: Email
        - textbox "Email" [ref=e20]:
          - /placeholder: you@example.com
          - text: test-1770435239308@example.com
      - generic [ref=e21]:
        - text: Organization Name
        - textbox "Organization Name" [ref=e23]:
          - /placeholder: Acme Research Lab
          - text: Test Org 1770435239308
      - generic [ref=e24]:
        - text: Password
        - textbox "Password" [ref=e26]: SecurePass123!
    - generic [ref=e27]:
      - button "Create Account" [ref=e28]
      - paragraph [ref=e29]:
        - text: Already have an account?
        - link "Sign in" [ref=e30] [cursor=pointer]:
          - /url: /login
```