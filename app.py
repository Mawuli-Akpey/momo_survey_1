# Distribution of "How many days did you operate your MOMO shop during the last 7 days/last week (labor supply)?"
plot_distribution("How many days did you operate your MOMO shop during the last 7 days/last week (labor supply)?", "Days Operated in the Last Week")

# Distribution of "What was the total MOMO business income earned during a typical month after paying all expenses?"
plot_distribution("What was the total MOMO business income earned during a typical month after paying all expenses?", "Distribution of MOMO Business Income")

# Bar Chart: Count of "Consider the last 30 days/ last month: have you ever refused or declined to make a transaction for a customer at your center for any of the reasons below?"
declined_transactions_count = df_filtered["Consider the last 30 days/ last month: have you ever refused or declined to make a transaction for a customer at your center for any of the reasons below?"].value_counts()
plot_annotated_bar(declined_transactions_count, "Reasons for Declining Transactions")

# Bar Chart: Count of "Which commission type is usually higher for you?"
commission_type_count = df_filtered["Which commission type is usually higher for you?"].value_counts()
plot_annotated_bar(commission_type_count, "Higher Commission Type")

