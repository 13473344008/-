//go:build t12_validation

package service

import (
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "testing"
 "github.com/google/uuid"
 "gorm.io/driver/sqlite"
 "gorm.io/gorm"
 "gorm.io/gorm/logger"
)

func TestT12LocalFaults(t *testing.T) {
 root:=os.Getenv("T12_RUNTIME")
 if root!="/path/to/ID/runtime/t12" {t.Fatal("exact isolated T12 runtime required")}
 db,e:=gorm.Open(sqlite.Open("file:"+root+"/db/passport-admin-t12.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"),&gorm.Config{Logger:logger.Default.LogMode(logger.Silent)});if e!=nil{t.Fatal(e)}
 pool,_:=db.DB();pool.SetMaxOpenConns(1);defer pool.Close()
 raw,e:=os.ReadFile(root+"/test-artifacts/fault-fixture.json");if e!=nil{t.Fatal(e)}
 var f struct{BatchID string `json:"batch_id"`;Target string `json:"target"`};if e=json.Unmarshal(raw,&f);e!=nil{t.Fatal(e)}
 s:=Publishing{};s.Orm=db;s.Admin=true;s.Actor=1
 for _,stage:=range []string{"build","rename","finalize"}{t.Run(stage,func(t *testing.T){
  must:=func(e error){t.Helper();if e!=nil{t.Fatal(e)}}
  state,e:=s.Status(f.BatchID);must(e)
  var code string;must(db.Table("batches").Select("batch_code").Where("id=?",f.BatchID).Scan(&code).Error)
  file:=filepath.Join(root,"publish/published",code+".json");old,e:=os.ReadFile(file);must(e)
  s.Fault=func(got string)error{if got==stage{return fmt.Errorf("T12 injected %s",stage)};return nil}
  r,e:=s.Rollback(f.BatchID,RollbackRequest{TargetRevisionID:f.Target,ExpectedCurrentRevisionID:&state.Current.ID,IdempotencyKey:uuid.NewString(),RollbackReason:"T12 isolated "+stage+" fault"});must(e);s.Fault=nil
  now,e:=os.ReadFile(file);must(e)
  if stage=="finalize" {
   if r.Record.PublishStatus!="recovery_required"||string(now)==string(old){t.Fatal("post switch state incorrect")}
   h,e:=s.Health(f.BatchID);must(e);if h.Classification!="file_switched_db_pending"{t.Fatal(h.Classification)}
   _,e=s.Rollback(f.BatchID,RollbackRequest{TargetRevisionID:f.Target,ExpectedCurrentRevisionID:&state.Current.ID,IdempotencyKey:uuid.NewString(),RollbackReason:"T12 must block"});if e==nil{t.Fatal("rollback bypassed recovery")}
   recovered,e:=s.ReconcileReason(f.BatchID,"T12 recover verified interrupted operation");must(e);if recovered.Record.ID!=r.Record.ID||recovered.Record.PublishStatus!="published"{t.Fatal("did not recover original operation")}
  } else if r.Record.PublishStatus!="failed"||string(now)!=string(old){t.Fatal("pre switch failure damaged current")}
 })}
}
