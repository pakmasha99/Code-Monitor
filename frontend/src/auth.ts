import NextAuth from "next-auth"
import GitHub from "next-auth/providers/github"

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true, // Allow IP address access for deployment
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: 'read:user user:email repo', // Request repo access to get repository info
        }
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      try {
        // Generate proper GitHub repo URL from username
        const github_username = profile?.login || profile?.username;
        const repo_url = github_username
          ? `https://github.com/${github_username}`
          : null;

        console.log('Registering user:', {
          name: user.name || profile?.name || 'Unknown',
          email: user.email || profile?.email,
          github_username,
          repo_url,
        });

        // Register user in FastAPI backend
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: user.name || profile?.name || 'Unknown',
            email: user.email || profile?.email || `${github_username}@github.com`,
            github_username,
            repo_url,
          }),
        });

        if (response.ok) {
          console.log('User registered successfully');
          return true;
        }

        if (response.status === 400) {
          const errorData = await response.json();
          console.log('User already exists:', errorData);
          return true; // Allow login even if user already exists
        }

        console.error('Failed to register user:', response.status, await response.text());
        return false;
      } catch (error) {
        console.error('Error during sign in:', error);
        return false;
      }
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub!;
      }
      return session;
    },
  },
  pages: {
    signIn: '/', // Redirect to home page for sign in
  },
})
