DROP TRIGGER final_command_purpose ON cv.command_result;
DROP TRIGGER final_erasure ON cv.erasure_request;
DROP TRIGGER erasure_policy_pin ON cv.erasure_request;
DROP FUNCTION cv.final_command_purpose_check();
DROP FUNCTION cv.final_erasure_check();
DROP FUNCTION cv.erasure_policy_pin();
ALTER TABLE cv.erasure_request DROP COLUMN erasure_policy_id;
