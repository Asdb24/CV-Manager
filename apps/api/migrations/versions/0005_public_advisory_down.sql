DROP FUNCTION cv.public_job(uuid),cv.accept_intake(text,uuid,uuid,uuid,text,text,text,boolean,uuid),
 cv.review_intake(uuid,uuid,integer,text,uuid,text,uuid),cv.publication_open(uuid,uuid);
DROP TABLE cv.advisory_review,cv.question_revision,cv.question_set,cv.advisory_finding_evidence,
 cv.advisory_finding,cv.advisory_evidence,cv.advisory_run,cv.advisory_task,cv.advisory_manifest_evidence,
 cv.advisory_manifest,cv.intake_review,cv.intake,cv.public_upload_grant,cv.publication,cv.publication_snapshot;
