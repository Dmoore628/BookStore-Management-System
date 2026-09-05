# Staff manual — Ledger & Spine

This is the counter computer program. It replaces the stock-card box, the cash-register tape notebook, and the special-order pad.

## Sign in

Open the address the manager posted (on this PC it is usually http://127.0.0.1:8000). Use the username you were given. If the screen sends you back to sign-in, your password is wrong or your account was turned off — ask the owner.

## Look up a book (stock cards)

Choose **Stock cards**. Search by title, author, ISBN, or shelf code (for example `F2-FIC`). On-hand quantity is the number you should be able to count on the shelf, unless a sale just happened.

Managers and the owner can add a new card, change title/author/price/shelf, or retire a title that you no longer sell. Retiring does not erase old sales.

Do not type a new quantity to “fix” a sale. Sales and incoming boxes change the number by themselves. If a cycle count is off, a manager records a **correction** (that is an audit line, not a silent edit).

## Sell a book (register)

1. Open **Register**.
2. Choose the title and how many copies.
3. Choose **cash** or **card**.
4. For cash, type the amount the customer handed you. The screen tells you the change.

Tax is whatever the store configured for this computer. You do not type a tax percent.

If the title does not have enough copies, the sale is refused. Count the shelf before arguing with the customer.

## Day drawer

Managers and the owner open **Day drawer** to see cash vs card totals for a date. Cashiers can sell; they cannot open this page.

## Incoming stock

When a publisher or Ingram box arrives, a manager opens **Incoming stock**, finds the pending order, and marks it **received**. The quantities on those titles go up.

## Special orders

Any signed-in staff member can log a customer name, a way to reach them, and the book they want. Cashiers see the name and title so they can take the request. Phone numbers and emails are hidden from cashiers; managers see them in order to call the customer.

Update the request to **ordered** when you have placed it with the supplier, and **fulfilled** when the customer has picked it up.

## If something looks wrong

Do not edit the database file. Tell the manager. They can write a backup from the floor page (owner/manager). Restoring a backup is a manager/owner job described in the business guide.
