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
const { ChartJSNodeCanvas } = require('chartjs-node-canvas');

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
// require('dotenv').config();
require('dotenv').config();
const mongoURI = process.env.MONGO_URI || "mongodb://localhost:27017/taskoffloader";
if (!mongoURI) {
  throw new Error("MONGO_URI is not defined in the environment variables");
}

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
    bucketName: "fs"
  });
});

// let gs;
// conn.once("open", () => {
//   // init stream
//   gs = new mongoose.mongo.GridFSBucket(conn.db, {
//     bucketName: ""
//   });
// });

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
          _id: uuidv4(), // Generate unique _id using uuid
          filename: filename,
          bucketName: "fs",
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
  req.files.forEach(file => {
    file._id = uuidv4(); // Generate unique id using uuid
  });
  req.files = req.files.filter(file => file.size <= 16 * 1024 * 1024);
  const conversionType = req.body.conversionType;

  // Add conversionType to each file document in the database
  req.files.forEach(async (file) => {
    await conn.db.collection('fs.files').updateOne(
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

const uri = process.env.MONGO_URI || "mongodb://localhost:27017/taskoffloader";
const client = new MongoClient(uri, { useNewUrlParser: true, useUnifiedTopology: true });

let db;
client.connect(err => {
  if (err) throw err;
  db = client.db("taskoffloader");
  gfs = new GridFSBucket(db, { bucketName: 'fs' });
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
        assigned_to: null, // edge or cloud
        operation: file.conversionType,
                     
      }));

    if (newTasks.length > 0) {
      await tasksCollection.insertMany(newTasks);
    }

    // res.status(200).json({ message: "Tasks scheduled successfully" });
    
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

// @route GET /computed_at/:id
// @desc  Get the computed_at value of a file from tasks collection using id
app.get("/computed_at/:id", async (req, res) => {
  try {
    const tasksCollection = conn.db.collection("tasks");
    const file = await tasksCollection.findOne({ _id: new mongoose.Types.ObjectId(req.params.id) });

    if (!file) {
      return res.status(404).json({
        err: "No file exists in tasks collection"
      });
    }

    return res.json({ assigned_to: file.assigned_to });
  } catch (err) {
    return res.status(500).json({ err: err.message });
  }
});

// @route GET /computed_at
// @desc  Get the computed_at value of all files from tasks collection
app.get("/computed_at", async (req, res) => {
  try {
    const tasksCollection = conn.db.collection("tasks");
    const files = await tasksCollection.find().toArray();

    if (!files || files.length === 0) {
      return res.status(404).json({
        err: "No files exist in tasks collection"
      });
    }

    const computedAtValues = files.map(file => ({
      _id: file._id,
      assigned_to: file.assigned_to
    }));

    return res.json(computedAtValues);
  } catch (err) {
    return res.status(500).json({ err: err.message });
  }
});

// @route GET /computed_at/count
// @desc  Get the count of files with computed_at="cloud" and computed_at="edge"
app.get("/computed_at_count", async (req, res) => {
  try {
    const tasksCollection = conn.db.collection("tasks");
    const cloudCount = await tasksCollection.countDocuments({ assigned_to: "cloud" });
    const edgeCount = await tasksCollection.countDocuments({ assigned_to: "Edge" });

    return res.json({
      cloud: cloudCount,
      edge: edgeCount
    });
  } catch (err) {
    return res.status(500).json({ err: err.message });
  }
});

// @route GET /filetype/:id
// @desc  Check the type of file (image or video) using id
app.get("/filetype_count", async (req, res) => {
  try {
    const filesCollection = conn.db.collection("fs.files");
    const imageCount = await filesCollection.countDocuments({ contentType: { $in: ["image/png", "image/jpeg"] } });
    const videoCount = await filesCollection.countDocuments({ contentType: { $in: ["video/mp4", "video/mpeg"] } });

    return res.json({
      images: imageCount,
      videos: videoCount
    });
  } catch (err) {
    return res.status(500).json({ err: err.message });
  }
});
const port = process.env.port || 5002;

// @route GET /file_sizes
// @desc  Get file size in MB of each file and time to complete the task
app.get("/file_sizes", async (req, res) => {
  try {
    const tasksCollection = conn.db.collection("tasks");
    const files = await tasksCollection.find().toArray();

    const tasksColl = conn.db.collection("fs.files");
    const fil = await tasksColl.find().toArray();

    if (!files || files.length === 0) {
      return res.status(404).json({
        err: "No files exist in tasks collection"
      });
    }

    const fileSizes = fil.map(file => {
      const sizeInMB = fil.length / (1024 * 1024); // Convert bytes to MB
      const timeToComplete = file.completed_at && file.started_at 
        ? (new Date(file.completed_at) - new Date(file.started_at)) / 1000 // Convert milliseconds to seconds
        : null;

      return {
        _id: file._id,
        filename: file.filename,
        sizeInMB: sizeInMB.toFixed(2),
        timeToComplete: timeToComplete ? timeToComplete + " seconds" : "Not completed"
      };
    });

    return res.json(fileSizes);
  } catch (err) {
    return res.status(500).json({ err: err.message });
  }
});

// @route GET /file_sizes_with_time
app.get("/file_sizes_with_time", async (req, res) => {
 try {
    const filesCollection = conn.db.collection("fs.files");
    const tasksCollection = conn.db.collection("tasks");
  
    const files = await filesCollection.find().toArray();
    const tasks = await tasksCollection.find().toArray();

    if (!files || files.length === 0) {
     return res.status(404).json({
        err: "No files exist in fs.files collection"
      });
    }

    const fileSizesWithTime = files.map(file => {
      const task = tasks.find(task => task._id.toString() === file._id.toString());
      const sizeInMB = file.length / (1024 * 1024); // Convert bytes to MB
      const timeToComplete = task && task.completed_at && task.started_at 
        ? (new Date(task.completed_at) - new Date(task.started_at)) / 1000 // Convert milliseconds to seconds
        : null;

      return {
        _id: file._id,
        filename: file.filename,
        sizeInMB: sizeInMB.toFixed(2),
        timeToComplete: timeToComplete ? timeToComplete + " seconds" : "Not completed"
      };
    });

    return res.json(fileSizesWithTime);
  } catch (err) {
     return res.status(500).json({ err: err.message });
  }});




app.listen(port, () => {
  console.log("server started on " + port);
});

