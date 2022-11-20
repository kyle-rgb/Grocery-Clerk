const { MongoClient, ObjectId } = require("mongodb")
const { Command } = require("commander");
require("dotenv").config()
const json_summary = require("json-summary");
var fs = require('fs')

function cleanup(object){
  Object.entries(object).forEach(([k, v])=>{
      if (v && typeof v ==='object'){
          cleanup(v);
      }
      if (v && typeof v ==='object' && !Object.keys(v).length || v===null || v === undefined || v === '' || k === '__typename' || v === 'none' || (Object.keys(object).length===1 && typeof v === 'boolean' && !v)) {
          if (Array.isArray(object)) {
              object.splice(k, 1)
          } else if (!(v instanceof Date)) {
              delete object[k];
          }
      }
  })
  return object
}

async function insertRun({functionName, collection, executor, args=undefined, push=false, _id=undefined , description=null, stats={}}){
    /**
   * @param functionName: the function being called
   * @param collection: the collection to insert run meta-data to
   * @param executor: how/where the function is being called from. i.e. the program 
   * @param args: Object representing function arguments
   * @param close: Boolean Switch Whether or Not to Close the Run Document and Calculate and Update Final MetaData into Collection
   * @param _id: ObjectId of current run to do update run; to mark completeion or append new function run into current run document.
   * @param description: Optional Additional Description to Append to Function Document.     
   */
  const client = new MongoClient(process.env.MONGO_CONN_URL);
  const dbName = 'new';
  var document, result; 
  await client.connect();
  console.log("Connected to Server")
  const db = client.db(dbName);
  const runCollection = db.collection(collection);
  let startedAt = new Date();
  if (_id) _id=new ObjectId(_id);
  let baseRunDocument = {
    function: functionName,
    duration: 0,
    startedAt: startedAt
  };
  if (args) baseRunDocument = {...baseRunDocument, ...args};
  if (description) baseRunDocument.description = description;
  // wrap functions metadata, determine type, get min started at, get total duration 
  if (_id){
    // updates top-level run time metrics 1st
    // @ every close function time must be incremented, duration must be incremented
    // subtract time to log function execution time
    // increment duration by this difference
    let filter = {"_id": _id} 
    let updateTotalRunFeatures = {
      "$set": { // update duration and endTime for Entire Run
        "duration": { 
          "$divide": [{"$subtract": [startedAt, "$startedAt"]}, 1000]
        },
        "endedAt": startedAt,
        "stats": stats
      }
    };
    let calculateFunctionTimes = {
        $set:  {
          "functions": {
              $map: {
                input: "$functions",
                in:{
                  $cond: {
                    if: {$eq: ["$$this", {$last: "$functions"}]},
                    then: {$mergeObjects: ["$$this", {"endedAt": startedAt, "duration": {"$divide" : [{$subtract: [startedAt, "$$this.startedAt"]}, 1000]}}]}, // timestamp end of function and calculate duration
                    else: "$$this"}
                  } 
              }
          }
        }
    }
    await runCollection.updateOne(filter, [updateTotalRunFeatures, calculateFunctionTimes]);
    console.log("updated 1 document in runs")
    if (push){
        // pushes next embedded function document into functions array of Run Document
        // push new function onto existing runs functions array with 0 duration
        await runCollection.updateOne(filter, {$push: {functions: baseRunDocument}});
        console.log("pushed 1 function on open run")
    }
    result =_id
  } else { // creates original run document 
    document = { //set the high level document features (executor, startedAt, durations & functions Array)
      executeVia: executor,
      startedAt: startedAt,
      duration: 0,
      functions: [ baseRunDocument ]
    }
    result = (await runCollection.insertOne(document)).insertedId
    console.log("inserted 1 document into ", collection)
    // returns inserted run document for update operations once function has successfully completed
  }
  await client.close(); 
  result = result.toString();
  console.log(`id=${result}`)
  return null
}

async function summarizeCollections(dbName){
  /**
   * 
  */
  const client = new MongoClient(process.env.MONGO_CONN_URL);
  await client.connect();
  console.log("Connected to Server")
  const db = client.db(dbName);
  let resultingDocument = {}; 
  let collections = db.listCollections({}, {nameOnly: true})
  // collections = await collections
  for await (let collection of collections){
    console.log(`starting ${collection.name}.....`)
    results = db.collection(collection.name).find({});
    results = await results.toArray(); 
    //results = cleanup(results)
    resultingDocument[collection.name] = json_summary.summarize(results, {arraySampleCount: results.length < 5000 ? results.length : 5000})
    console.log(`finished ${collection.name}.....`)
  }

  fs.writeFileSync("../../data/summary.json", JSON.stringify(resultingDocument, null, 3))
  await client.close()
  return null
}





const program = new Command();

program
    .command("insert")
    .description("inserts function run into collection")
    .option("-f, --function-name <name>", "function name to execute")
    .option("-c, --collection [name]", "mongo collection name", "runs")
    .option("-e, --executor <program>", "program calling scraping function")
    .option("-i, --_id <ObjectId>", "mongoDB created ObjectId generated by an initial call to insert")
    .option("-d, --description <description>", "Optional Description to Add to Run Document")
    .option("-s, --stats <stats>", "stats snapshot from started container for full run")
    .option("--args [additionalArgs]", "any additional metadata to insert into document. Only Accepts a single JSON-quoted string of type '{\"variableName\": value}'. Is parsed before insertion.")
    .option("--push", "mark previous function in run as complete and push new function onto run stack")
    .action((options)=> {
        console.log(options)
        options.args ? options.args = cleanup(JSON.parse(options.args)) : undefined ;
        options.stats ? options.stats = cleanup(JSON.parse(options.stats)) : undefined; 
        insertRun(options)
        return 0
    })

program
    .command("test")
    .description("runs a sample command with a 5 second sleeper to test docker logs")
    .option("-d, --data [data]", "data to pass", {})
    .action(async (options)=> {
      // await createSampleCommand(options)
      // console.log(cleanup(JSON.parse(options.data)))
      await summarizeCollections("new")
      return 0
    })
program.parse();