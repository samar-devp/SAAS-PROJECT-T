# Comprehensive API Summary

## Total APIs Created: 100+

### AuthN Module (18 APIs)
1. `POST /api/change-password/<user_id>` - Change password for all roles
2. `GET /api/employee/<org_id>` - Employee list under admin
3. `GET /api/organization_all_admin/<orgID>` - All admins under organization
4. `GET /api/all_employees/<org_id>` - All employees under organization
5. `POST /api/user_deactivate/<org_id>/<unqID>` - Deactivate employee
6. `PUT /api/employee_profile_update/<org_id>/<unqID>` - Update employee profile
7. `POST /api/emp_transfer/<org_id>` - Transfer employee to another admin
8. `GET /api/admin_detail_csv/<org_id>` - Download admin details CSV
9. `GET /api/deactivate_list/<org_id>` - Get deactivated users list
10. `PUT /api/deactivate_list_update/<clnID>` - Bulk activate/deactivate
11. `GET /api/all_user_list_info/<userID>` - All user list info
12. `GET /api/all_user_device_info/<userID>` - All user device info
13. `POST /api/employee_status_update/<clnID>/<date>` - Update employee status
14. `PUT /api/employee_fencing_update/<clnID>/<unqID>` - Update geo-fencing
15. `GET /api/employee_profile/<clnID>` - All employee profiles
16. `POST /api/employee_bulk_deactivate/<clnID>` - Bulk deactivate employees
17. `GET /api/search_employee/<orgID>` - Global employee search
18. `GET /api/dashboard/organization/<org_id>` - Organization dashboard
19. `GET /api/dashboard/admin/<admin_id>` - Admin dashboard

### Payroll System (8 APIs)
20. `GET /api/payroll/dashboard/<org_id>` - Payroll dashboard
21. `GET /api/payroll/employee-history/<org_id>/<employee_id>` - Employee payroll history
22. `GET /api/payroll/summary/<org_id>` - Payroll summary
23. `GET /api/payroll/advances/<org_id>` - Employee advances list
24. `GET /api/payroll/advances/<org_id>/<employee_id>` - Employee advances by employee
25. `GET /api/payroll/bank-info-list/<org_id>` - Bank information list
26. `POST /api/payroll/generate-payroll/<org_id>` - Generate payroll
27. `GET /api/payroll/payroll-monthly-report/<org_id>/<month>/<year>` - Monthly report

### Leave Management (6 APIs)
28. `GET /api/leave/dashboard/<org_id>` - Leave dashboard
29. `GET /api/leave/leave-balances-list/<org_id>` - Leave balances list
30. `GET /api/leave/leave-balances-list/<org_id>/<employee_id>` - Leave balances by employee
31. `GET /api/leave/applications-list/<org_id>` - Leave applications list
32. `POST /api/leave/leave-approval/<application_id>` - Approve/reject leave
33. `GET /api/leave/leave-reports/<admin_id>` - Leave reports

### Attendance/WorkLog (6 APIs)
34. `GET /api/dashboard/<org_id>` - Attendance dashboard
35. `GET /api/employee-history/<org_id>/<employee_id>` - Employee attendance history
36. `GET /api/summary/<org_id>` - Attendance summary
37. `POST /api/attendance-check/<userid>` - Check in/out
38. `GET /api/employee-attendance/<admin_id>` - Fetch employee attendance
39. `PUT /api/edit-attendance/<userid>/<attendance_id>` - Edit attendance

### Expense Management (9 APIs)
40. `GET /api/expenses-list/<org_id>` - Expenses list
41. `GET /api/employee-expenses/<org_id>/<employee_id>` - Employee expenses
42. `GET /api/reimbursements-list/<org_id>` - Reimbursements list
43. `GET /api/expense-dashboard/<admin_id>` - Expense dashboard
44. `POST /api/expense-approval/<expense_id>` - Approve/reject expense
45. `POST /api/expense-reimbursement/<admin_id>` - Create reimbursement
46. `GET /api/expense-budget/<admin_id>` - Budget management
47. `GET /api/expense-categories/<admin_id>` - Expense categories
48. `POST /api/expenses/<admin_id>` - Create expense

### Task Management (9 APIs)
49. `GET /api/tasks/dashboard/<org_id>` - Task dashboard
50. `GET /api/tasks/employee-tasks/<org_id>/<employee_id>` - Employee tasks
51. `GET /api/tasks/projects-list/<org_id>` - Projects list
52. `GET /api/tasks/projects/<admin_id>` - Projects CRUD
53. `GET /api/tasks/tasks/<admin_id>` - Tasks CRUD
54. `GET /api/tasks/task-comments/<task_id>` - Task comments
55. `GET /api/tasks/task-time-logs/<task_id>` - Task time logs
56. `GET /api/tasks/task-types/<admin_id>` - Task types
57. `GET /api/tasks/task-reports/<admin_id>` - Task reports

### Visit Management (8 APIs)
58. `GET /api/visit/dashboard/<org_id>` - Visit dashboard
59. `GET /api/visit/employee-visits/<org_id>/<employee_id>` - Employee visits
60. `GET /api/visit/visits/<admin_id>` - Visits CRUD
61. `POST /api/visit/visit-start-end/<visit_id>` - Start/end visit
62. `GET /api/visit/visit-templates/<admin_id>` - Visit templates
63. `GET /api/visit/visit-reports/<admin_id>` - Visit reports
64. `GET /api/visit/visit-expenses/<visit_id>` - Visit expenses
65. `GET /api/visit/visit-reminders/<visit_id>` - Visit reminders

### Asset Management (8 APIs)
66. `GET /api/asset/dashboard/<org_id>` - Asset dashboard
67. `GET /api/asset/employee-assets/<org_id>/<employee_id>` - Employee assets
68. `GET /api/asset/assets/<org_id>` - Assets CRUD
69. `GET /api/asset/asset-categories/<org_id>` - Asset categories
70. `POST /api/asset/asset-maintenance/<asset_id>` - Asset maintenance
71. `POST /api/asset/asset-transfer/<asset_id>` - Asset transfer
72. `GET /api/asset/asset-reports/<org_id>` - Asset reports
73. `GET /api/asset/asset-depreciation/<asset_id>` - Asset depreciation

### Notes Management (7 APIs)
74. `GET /api/notes/dashboard/<org_id>` - Notes dashboard
75. `GET /api/notes/employee-notes/<org_id>/<employee_id>` - Employee notes
76. `GET /api/notes/notes/<user_id>` - Notes CRUD
77. `GET /api/notes/note-categories/<org_id>` - Note categories
78. `GET /api/notes/note-comments/<note_id>` - Note comments
79. `GET /api/notes/note-templates/<org_id>` - Note templates
80. `GET /api/notes/note-search/<org_id>` - Search notes

### Broadcast Management (6 APIs)
81. `GET /api/broadcast/dashboard/<org_id>` - Broadcast dashboard
82. `GET /api/broadcast/broadcasts-list/<org_id>` - Broadcasts list
83. `GET /api/broadcast/broadcasts/<org_id>` - Broadcasts CRUD
84. `GET /api/broadcast/broadcast-recipients/<broadcast_id>` - Broadcast recipients
85. `GET /api/broadcast/broadcast-templates/<org_id>` - Broadcast templates
86. `GET /api/broadcast/broadcast-analytics/<org_id>` - Broadcast analytics

### Notification Management (7 APIs)
87. `GET /api/notification/dashboard/<org_id>` - Notification dashboard
88. `GET /api/notification/user-notifications/<user_id>` - User notifications
89. `PUT /api/notification/user-notifications/<user_id>/<notification_id>` - Mark as read
90. `GET /api/notification/notifications/<user_id>` - Notifications CRUD
91. `GET /api/notification/notification-preferences/<user_id>` - Notification preferences
92. `POST /api/notification/notifications-mark-all-read/<user_id>` - Mark all as read
93. `GET /api/notification/notification-templates/<org_id>` - Notification templates

### Helpdesk Management (7 APIs)
94. `GET /api/helpdesk/dashboard/<org_id>` - Helpdesk dashboard
95. `GET /api/helpdesk/assigned-tickets/<org_id>/<user_id>` - Assigned tickets
96. `GET /api/helpdesk/tickets/<org_id>` - Tickets CRUD
97. `GET /api/helpdesk/categories/<org_id>` - Ticket categories
98. `GET /api/helpdesk/tickets/<ticket_id>/comments` - Ticket comments
99. `GET /api/helpdesk/sla-policies/<org_id>` - SLA policies
100. `GET /api/helpdesk/assignment-rules/<org_id>` - Assignment rules

### Performance Management (8 APIs)
101. `GET /api/performance/dashboard/<org_id>` - Performance dashboard
102. `GET /api/performance/okrs/<org_id>` - OKRs CRUD
103. `GET /api/performance/kpis/<org_id>` - KPIs CRUD
104. `GET /api/performance/reviews/<org_id>` - Performance reviews
105. `GET /api/performance/review-cycles/<org_id>` - Review cycles
106. `GET /api/performance/goals/<org_id>` - Goal library
107. `GET /api/performance/rating-matrix/<org_id>` - Rating matrix
108. `GET /api/performance/review-360/<org_id>` - 360 reviews

### Onboarding Management (8 APIs)
109. `GET /api/onboarding/dashboard/<org_id>` - Onboarding dashboard
110. `GET /api/onboarding/templates/<org_id>` - Onboarding templates
111. `GET /api/onboarding/processes/<org_id>` - Onboarding processes
112. `GET /api/onboarding/tasks/<process_id>` - Onboarding tasks
113. `GET /api/onboarding/document-types/<org_id>` - Document types
114. `GET /api/onboarding/documents/<employee_id>` - Employee documents
115. `GET /api/onboarding/checklists/<template_id>` - Checklists
116. `GET /api/onboarding/processes/<org_id>/<pk>` - Process details

### HR Analytics (6 APIs)
117. `GET /api/analytics/dashboard/<org_id>` - Analytics dashboard
118. `GET /api/analytics/attendance/<org_id>` - Attendance analytics
119. `GET /api/analytics/attrition/<org_id>` - Attrition records
120. `GET /api/analytics/salary-distribution/<org_id>` - Salary distribution
121. `GET /api/analytics/cost-centers/<org_id>` - Cost centers
122. `GET /api/analytics/cost-center-analytics/<org_id>` - Cost center analytics

### Organization Management (6 APIs)
123. `GET /api/organization/plans` - Subscription plans
124. `GET /api/organization/subscriptions/<org_id>` - Organization subscriptions
125. `GET /api/organization/modules/<org_id>` - Organization modules
126. `GET /api/organization/usage/<org_id>` - Usage statistics
127. `POST /api/organization/deactivate/<org_id>` - Deactivate organization
128. `GET /api/organization/deactivation-logs/<org_id>` - Deactivation logs

## API Categories

### Dashboard APIs (15)
- Organization Dashboard
- Admin Dashboard
- Payroll Dashboard
- Leave Dashboard
- Attendance Dashboard
- Expense Dashboard
- Task Dashboard
- Visit Dashboard
- Asset Dashboard
- Notes Dashboard
- Broadcast Dashboard
- Notification Dashboard
- Helpdesk Dashboard
- Performance Dashboard
- Onboarding Dashboard
- Analytics Dashboard

### List APIs (30+)
- Employee lists (by admin, by organization)
- Admin lists
- Task lists
- Expense lists
- Leave applications
- Attendance history
- Payroll history
- Asset lists
- Visit lists
- Notes lists
- Broadcast lists
- Notification lists
- Ticket lists
- And more...

### CRUD APIs (40+)
- All major entities have full CRUD operations
- Employee management
- Payroll management
- Leave management
- Task management
- Asset management
- And more...

### Utility APIs (15+)
- Search APIs
- Export APIs (CSV, Excel)
- Bulk operations
- Status updates
- Transfer operations
- And more...

## Total: 128+ APIs

All APIs follow RESTful conventions and include:
- Proper authentication
- Pagination support
- Filtering and search
- Error handling
- Consistent response format
- Comprehensive documentation

