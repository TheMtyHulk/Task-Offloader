const express = require("express");
const app = express();
const cors=require('cors')
const crypto = require("crypto");
const path = require("path");
const mongoose = require("mongoose");
const multer = require("multer");
const GridFsStorage = require("multer-gridfs-storage");
const { v4: uuidv4 } = require('uuid');
const { MongoClient } = require('mongodb');
const GridFSBucket = require('mongodb').GridFSBucket;

// Middlewares
app.use(express.json());
app.set("view engine", "ejs");

// Set static folder
app.use(express.static(path.join(__dirname, "views")));
app.use('/controllers', express.static(path.join(__dirname, 'controllers')));

// Load index.html
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "views", "index.html"));
});
// DB
const mongoURI = "mongodb://localhost:27017/taskoffloader";

// connection
const conn = mongoose.createConnection(mongoURI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

app.use(cors({
  methods:'POST',
  origin:'*'
}))

// init gfs
let gfs;
conn.once("open", () => {
  // init stream
  gfs = new mongoose.mongo.GridFSBucket(conn.db, {
    bucketName: "uploads"
  });
});
// Middleware to generate UUID for each file

// Storage
const storage = new GridFsStorage({
  url: mongoURI,
  file: (req, file) => {
    return new Promise((resolve, reject) => {
      crypto.randomBytes(16, (err, buf) => {
        if (err) {
          return reject(err);
        }
        const filename = file.originalname;
        const fileInfo = {
          // Generate UUID for file ID
          filename: filename,
          bucketName: "uploads",
          
        };
        resolve(fileInfo);
      });
    });
  }
});

const upload = multer({
  storage
});

// get / page
app.get("/", (req, res) => {
  if(!gfs) {
    console.log("some error occured, check connection to db");
    res.send("some error occured, check connection to db");
    process.exit(0);
  }
  gfs.find().toArray((err, files) => {
    // check if files
    if (!files || files.length === 0) {
      return res.render("index", {
        files: false
      });
    } else {
      const f = files
        .map(file => {
          if (
            file.contentType === "image/png" ||
            file.contentType === "image/jpeg"
          ) {
            file.isImage = true;
          } else {
            file.isImage = false;
          }
          return file;
        })
        .sort((a, b) => {
          return (
            new Date(b["uploadDate"]).getTime() -
            new Date(a["uploadDate"]).getTime()
          );
        });

      return res.render("index", {
        files: f
      });
    }

    // return res.json(files);
  });
});

app.post("/upload", upload.array("files", 10), (req, res) => {
  // filter out the files that exceeds the size limit of 16 mb
  req.files = req.files.filter(file => file.size <= 16 * 1024 * 1024);
  const conversionType = req.body.conversionType;

  // Add conversionType to each file document in the database
  req.files.forEach(async (file) => {
    await conn.db.collection('uploads.files').updateOne(
      { _id: file.id },
      { $set: { conversionType: conversionType } }
    );
  });
  if (req.files.length === 0) {
    return res.status(400).json({ error: "All files exceed the size limit of 16MB." });
  }
  for (const file of req.files) {
    if (file.size > 16 * 1024 * 1024) { // 16MB in bytes
      return res.status(400).json({ error: "File size should be less than 16MB." });
    }
  }
  if (req.files.length > 0) {
    res.redirect("/");
    // res.status(200).json({ message: "Files uploaded successfully", conversionType });
  } else {
    res.status(400).json({ error: "Please upload at least one file." });
  }
});

const uri = "mongodb://localhost:27017/taskoffloader";
const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });

let db;
client.connect(err => {
  if (err) throw err;
  db = client.db("taskoffloader");
  gfs = new GridFSBucket(db, { bucketName: 'uploads' });
});

// to schedule tasks
app.post("/schedule-tasks", async (req, res) => {
  try {
    const files = await gfs.find().toArray();
    if (!files || files.length === 0) {
      return res.status(404).json({ err: "No files exist" });
    }

    const tasksCollection = conn.db.collection("tasks");
    await tasksCollection.createIndex({ "scheduled_at": 1 });

    const existingTasks = await tasksCollection.find({ _id: { $in: files.map(file => file._id) } }).toArray();
    const existingTaskIds = new Set(existingTasks.map(task => task._id.toString()));

    const newTasks = files
      .filter(file => !existingTaskIds.has(file._id.toString()))
      .map(file => ({
        _id: file._id,
        command: file.filename,
        scheduled_at: new Date(),
        picked_at: null,
        started_at: null,
        completed_at: null,
        completed_by: null,
        computed_at: null, // edge or cloud
        operation: file.conversionType,
                     
      }));

    if (newTasks.length > 0) {
      await tasksCollection.insertMany(newTasks);
    }

    res.status(200).json({ message: "Tasks scheduled successfully" });
    
  } catch (err) {
    res.status(500).json({ err: err.message });
  }
});


// @route GET /files
// @desc  Display all the files in JSON

app.get("/files", (req, res) => {
  gfs.find().toArray((err, files) => {
    // check if files
    if (!files || files.length === 0) {
      return res.status(404).json({
        err: "no files exist"
      });
    } 

    return res.json(files);
  });
});

// to fetch file using filename 
app.get("/files/:filename", (req, res) => {
    const file = gfs
    .find({
      filename: req.params.filename
    })
    .toArray((err, files) => {
      if (!files || files.length === 0) {
        return res.status(404).json({
          err: "no files exist"
        });
      }
      gfs.openDownloadStreamByName(req.params.filename).pipe(res);
    });
});


app.get("/image/:filename", (req, res) => {
  console.log('id', req.params.id)
  const file = gfs
    .find({
      filename: req.params.filename
    })
    .toArray((err, files) => {
      if (!files || files.length === 0) {
        return res.status(404).json({
          err: "no files exist"
        });
      }
      gfs.openDownloadStreamByName(req.params.filename).pipe(res);
    });
});

// files/del/:id
// Delete chunks from the db
app.post("/files/del/:id", (req, res) => {
  const tasksCollection = conn.db.collection("tasks");
  tasksCollection.deleteOne({ _id: new mongoose.Types.ObjectId(req.params.id) });
  gfs.delete(new mongoose.Types.ObjectId(req.params.id), (err, data) => {
    if (err) return res.status(404).json({ err: err.message });
    res.redirect("/");
  });
});



// @route GET /file/:id
// @desc  Display single file object
app.get("/file/:id", (req, res) => {
  gfs.find({ _id: new mongoose.Types.ObjectId(req.params.id) }).toArray((err, files) => {
    if (!files || files.length === 0) {
      return res.status(404).json({
        err: "no files exist"
      });
    }
    return res.json(files[0]);
  });
});

// @route GET /filedetails/:id
// @desc  Display single file object from tasks collection using id
app.get("/filedetails/:id", async (req, res) => {
  try {
    const tasksCollection = conn.db.collection("tasks");
    const file = await tasksCollection.findOne({ _id: new mongoose.Types.ObjectId(req.params.id) });

    if (!file) {
      return res.status(404).json({
        err: "No file exists in tasks collection"
      });
    }

    return res.json(file);
  } catch (err) {
    return res.status(500).json({ err: err.message });
  }
});

const port = 5002;

app.listen(port, () => {
  console.log("server started on " + port);
});
