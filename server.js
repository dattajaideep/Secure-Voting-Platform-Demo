import express from "express";
import mongoose from "mongoose";
import bcrypt from "bcrypt";
import session from "express-session";

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(session({ secret: "yoursecret", resave: false, saveUninitialized: true }));

// MongoDB connection
mongoose.connect("mongodb://localhost:27017/securevote");

// User schema
const UserSchema = new mongoose.Schema({
  name: String,
  email: { type: String, unique: true },
  password: String
});
const User = mongoose.model("User", UserSchema);

// Register route
app.post("/register", async (req, res) => {
  const { name, email, password } = req.body;
  const hashed = await bcrypt.hash(password, 10);
  try {
    await User.create({ name, email, password: hashed });
    res.send("✅ User registered! <a href='/'>Login here</a>");
  } catch (err) {
    res.send("❌ Error: " + err.message);
  }
});

// Login route
app.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findOne({ email });
  if (user && await bcrypt.compare(password, user.password)) {
    req.session.user = user;
    res.send("✅ Login successful! <a href='/'>Go to homepage</a>");
  } else {
    res.send("❌ Invalid email or password");
  }
});

app.listen(3000, () => console.log("🚀 Server running on http://localhost:3000"));
