import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

cli = typer.Typer()

@cli.command()
def initialize():
    """Initialize the database by dropping all tables, recreating them, and adding a default user 'bob'."""
    with get_session() as db:  # Get a connection to the database
        drop_all()  # delete all tables
        create_db_and_tables()  # recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass')  # Create a new user (in memory)
        db.add(bob)  # Tell the database about this new data
        db.commit()  # Tell the database persist the data
        db.refresh(bob)  # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(
    username: str = typer.Argument(..., help="Exact username to search for")
):
    """Get a user by exact username match."""
    with get_session() as db:  # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def find_user(
    search_term: str = typer.Argument(..., help="Partial email or username to search for")
):
    """Find users using partial match of their email OR username."""
    with get_session() as db:
        users = db.exec(
            select(User).where(
                or_(
                    User.username.contains(search_term),
                    User.email.contains(search_term)
                )
            )
        ).all()
        
        if not users:
            print(f'No users found matching "{search_term}"')
            return
        
        print(f'Found {len(users)} user(s) matching "{search_term}":')
        for user in users:
            print(user)

@cli.command()
def get_all_users():
    """Get all users in the database."""
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def list_users(
    limit: int = typer.Option(10, "--limit", "-l", min=1, help="Maximum number of users to return"),
    offset: int = typer.Option(0, "--offset", "-o", min=0, help="Number of users to skip")
):
    """List first N users with pagination support."""
    with get_session() as db:
        users = db.exec(
            select(User).offset(offset).limit(limit)
        ).all()
        
        if not users:
            print(f"No users found for offset={offset}, limit={limit}")
            return
        
        print(f"Users {offset+1}-{offset+len(users)} of {limit} (offset={offset}):")
        for user in users:
            print(user)

@cli.command()
def change_email(
    username: str = typer.Argument(..., help="Username of user to update"),
    new_email: str = typer.Argument(..., help="New email address")
):
    """Change a user's email address."""
    with get_session() as db:  # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: str = typer.Argument(..., help="Username for new user"),
    email: str = typer.Argument(..., help="Email address for new user"),
    password: str = typer.Argument(..., help="Password for new user")
):
    """Create a new user with username, email, and password."""
    with get_session() as db:  # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback()  # let the database undo any previous steps of a transaction
            print("Username or email already taken!")  # give the user a useful message
        else:
            print(newuser)  # print the newly created user

@cli.command()
def delete_user(
    username: str = typer.Argument(..., help="Username of user to delete")
):
    """Delete a user by username."""
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

if __name__ == "__main__":
    cli()
