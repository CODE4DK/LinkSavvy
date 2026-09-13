export interface paths {
    "/api/v1/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_api_v1_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/verify-email": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Email */
        post: operations["verify_email_api_v1_auth_verify_email_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/resend-verification": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resend Verification */
        post: operations["resend_verification_api_v1_auth_resend_verification_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh */
        post: operations["refresh_api_v1_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout-all": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout All */
        post: operations["logout_all_api_v1_auth_logout_all_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sessions */
        get: operations["list_sessions_api_v1_auth_sessions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Session */
        delete: operations["delete_session_api_v1_auth_sessions__session_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/forgot-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Forgot Password */
        post: operations["forgot_password_api_v1_auth_forgot_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/reset-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Password */
        post: operations["reset_password_api_v1_auth_reset_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/change-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Password */
        post: operations["change_password_api_v1_auth_change_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/linkedin/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Linkedin Start */
        get: operations["linkedin_start_api_v1_auth_linkedin_start_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/linkedin/callback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Linkedin Callback */
        get: operations["linkedin_callback_api_v1_auth_linkedin_callback_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_api_v1_me_get"];
        put?: never;
        post?: never;
        /** Delete Me */
        delete: operations["delete_me_api_v1_me_delete"];
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_api_v1_me_patch"];
        trace?: never;
    };
    "/api/v1/profile/connect": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Connect */
        post: operations["connect_api_v1_profile_connect_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/connect/callback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Connect Callback */
        get: operations["connect_callback_api_v1_profile_connect_callback_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/sync": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Sync */
        post: operations["sync_api_v1_profile_sync_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/sync/commit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Commit Sync */
        post: operations["commit_sync_api_v1_profile_sync_commit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/imports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Paste Import */
        post: operations["create_paste_import_api_v1_profile_imports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/imports/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Upload Import */
        post: operations["create_upload_import_api_v1_profile_imports_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/imports/{import_id}/commit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Commit Import */
        post: operations["commit_import_api_v1_profile_imports__import_id__commit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/snapshot": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Current Snapshot */
        get: operations["get_current_snapshot_api_v1_profile_snapshot_get"];
        /** Put Manual Snapshot */
        put: operations["put_manual_snapshot_api_v1_profile_snapshot_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/snapshots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Snapshots */
        get: operations["get_snapshots_api_v1_profile_snapshots_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/profile/snapshots/{version_a}/diff/{version_b}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Snapshot Diff */
        get: operations["get_snapshot_diff_api_v1_profile_snapshots__version_a__diff__version_b__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/metrics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Gateway Metrics */
        get: operations["get_gateway_metrics_internal_metrics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/playground/prompts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Playground Prompts */
        get: operations["list_playground_prompts_internal_playground_prompts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/playground/run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run Playground Prompt */
        post: operations["run_playground_prompt_internal_playground_run_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/internal/playground/stream": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Stream Playground Prompt */
        post: operations["stream_playground_prompt_internal_playground_stream_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs/{job_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Job Status */
        get: operations["get_job_status_api_v1_jobs__job_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audits": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Audit */
        post: operations["start_audit_api_v1_audits_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audits/latest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Latest */
        get: operations["get_latest_api_v1_audits_latest_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audits/{audit_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Audit */
        get: operations["get_audit_api_v1_audits__audit_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/scores/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Score History Endpoint */
        get: operations["get_score_history_endpoint_api_v1_scores_history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/recommendations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Recommendations */
        get: operations["get_recommendations_api_v1_recommendations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/recommendations/{recommendation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Recommendation */
        patch: operations["update_recommendation_api_v1_recommendations__recommendation_id__patch"];
        trace?: never;
    };
    "/api/v1/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Dashboard */
        get: operations["get_dashboard_api_v1_dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tools */
        get: operations["list_tools_api_v1_tools_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/{tool_id}/run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run Tool */
        post: operations["run_tool_api_v1_tools__tool_id__run_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/{tool_id}/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tool Runs */
        get: operations["list_tool_runs_api_v1_tools__tool_id__runs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}/regenerate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Regenerate Tool Run */
        post: operations["regenerate_tool_run_api_v1_tools_runs__run_id__regenerate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}/rate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Rate Tool Run */
        post: operations["rate_tool_run_api_v1_tools_runs__run_id__rate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tools/runs/{run_id}/save": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Save Tool Run */
        post: operations["save_tool_run_api_v1_tools_runs__run_id__save_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content/voice": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Voice Profile */
        get: operations["get_voice_profile_api_v1_content_voice_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content/voice/samples": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Pasted Samples */
        post: operations["submit_pasted_samples_api_v1_content_voice_samples_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content/voice/samples/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Uploaded Samples */
        post: operations["submit_uploaded_samples_api_v1_content_voice_samples_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Asset Endpoint */
        post: operations["create_asset_endpoint_api_v1_assets_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/assets/{asset_id}/mark-posted": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Asset Posted */
        post: operations["mark_asset_posted_api_v1_assets__asset_id__mark_posted_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Carousel Endpoint */
        post: operations["create_carousel_endpoint_api_v1_carousels_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels/{asset_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Carousel Endpoint */
        get: operations["get_carousel_endpoint_api_v1_carousels__asset_id__get"];
        /** Update Carousel Endpoint */
        put: operations["update_carousel_endpoint_api_v1_carousels__asset_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels/{asset_id}/export/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Carousel Pdf Endpoint */
        post: operations["export_carousel_pdf_endpoint_api_v1_carousels__asset_id__export_pdf_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/carousels/{asset_id}/export/png": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Carousel Png Endpoint */
        post: operations["export_carousel_png_endpoint_api_v1_carousels__asset_id__export_png_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Plans Endpoint */
        get: operations["list_plans_endpoint_api_v1_content_plans_get"];
        put?: never;
        /** Create Plan Endpoint */
        post: operations["create_plan_endpoint_api_v1_content_plans_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/consistency": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Consistency Endpoint */
        get: operations["consistency_endpoint_api_v1_content_plans_consistency_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/performance-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Performance Summary Endpoint */
        get: operations["performance_summary_endpoint_api_v1_content_plans_performance_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Plan Endpoint */
        get: operations["get_plan_endpoint_api_v1_content_plans__plan_id__get"];
        put?: never;
        post?: never;
        /** Delete Plan Endpoint */
        delete: operations["delete_plan_endpoint_api_v1_content_plans__plan_id__delete"];
        options?: never;
        head?: never;
        /** Update Plan Endpoint */
        patch: operations["update_plan_endpoint_api_v1_content_plans__plan_id__patch"];
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/reschedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reschedule Plan Endpoint */
        post: operations["reschedule_plan_endpoint_api_v1_content_plans__plan_id__reschedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/reminder": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Reminder Endpoint */
        post: operations["set_reminder_endpoint_api_v1_content_plans__plan_id__reminder_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/mark-posted": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Posted Endpoint */
        post: operations["mark_posted_endpoint_api_v1_content_plans__plan_id__mark_posted_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/{plan_id}/performance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Record Performance Endpoint */
        post: operations["record_performance_endpoint_api_v1_content_plans__plan_id__performance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/recurring-slots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Recurring Slots Endpoint */
        post: operations["recurring_slots_endpoint_api_v1_content_plans_recurring_slots_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/content-plans/bulk-schedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Bulk Schedule Endpoint */
        post: operations["bulk_schedule_endpoint_api_v1_content_plans_bulk_schedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/parse/paste": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Parse Resume Paste Endpoint */
        post: operations["parse_resume_paste_endpoint_api_v1_career_resumes_parse_paste_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/parse/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Parse Resume Upload Endpoint */
        post: operations["parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/from-profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Parse Resume From Profile Endpoint */
        post: operations["parse_resume_from_profile_endpoint_api_v1_career_resumes_from_profile_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Resumes Endpoint */
        get: operations["list_resumes_endpoint_api_v1_career_resumes_get"];
        put?: never;
        /** Commit Resume Endpoint */
        post: operations["commit_resume_endpoint_api_v1_career_resumes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Resume Endpoint */
        get: operations["get_resume_endpoint_api_v1_career_resumes__resume_id__get"];
        put?: never;
        post?: never;
        /** Delete Resume Endpoint */
        delete: operations["delete_resume_endpoint_api_v1_career_resumes__resume_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate Resume Endpoint */
        post: operations["activate_resume_endpoint_api_v1_career_resumes__resume_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}/export/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Resume Pdf Endpoint */
        post: operations["export_resume_pdf_endpoint_api_v1_career_resumes__resume_id__export_pdf_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/resumes/{resume_id}/export/docx": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Export Resume Docx Endpoint */
        post: operations["export_resume_docx_endpoint_api_v1_career_resumes__resume_id__export_docx_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/job-descriptions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Job Descriptions Endpoint */
        get: operations["list_job_descriptions_endpoint_api_v1_career_job_descriptions_get"];
        put?: never;
        /** Create Job Description Endpoint */
        post: operations["create_job_description_endpoint_api_v1_career_job_descriptions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/job-descriptions/{job_description_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Job Description Endpoint */
        get: operations["get_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__get"];
        put?: never;
        post?: never;
        /** Delete Job Description Endpoint */
        delete: operations["delete_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/career/matches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Matches Endpoint */
        get: operations["list_matches_endpoint_api_v1_career_matches_get"];
        put?: never;
        /** Create Match Endpoint */
        post: operations["create_match_endpoint_api_v1_career_matches_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AssetResponse */
        AssetResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Body Format */
            body_format: string;
            /** Source Tool Run Id */
            source_tool_run_id: string | null;
            /** Folder Id */
            folder_id: string | null;
            /** Metadata */
            metadata: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * AssetType
         * @enum {string}
         */
        AssetType: "post" | "headline" | "about" | "experience_bullets" | "comment" | "message" | "resume" | "cover_letter" | "job_description" | "analysis" | "conversation" | "template" | "carousel" | "roadmap";
        /** AuditCategoryResultResponse */
        AuditCategoryResultResponse: {
            /** Category */
            category: string;
            /** Score */
            score: number | null;
            /** Status */
            status: string;
            /** Inputs Available */
            inputs_available: {
                [key: string]: unknown;
            };
            /** Detail */
            detail: {
                [key: string]: unknown;
            };
            /** Findings */
            findings: components["schemas"]["AuditFindingResponse"][];
        };
        /** AuditDetailResponse */
        AuditDetailResponse: {
            /** Id */
            id: string;
            /** Status */
            status: string;
            /** Scoring Version */
            scoring_version: string;
            /** Overall Score */
            overall_score: number | null;
            /** Trigger */
            trigger: string;
            /** Started At */
            started_at: string | null;
            /** Completed At */
            completed_at: string | null;
            /** Duration Ms */
            duration_ms: number | null;
            /** Error */
            error: string | null;
            /** Categories */
            categories: components["schemas"]["AuditCategoryResultResponse"][];
        };
        /** AuditFindingResponse */
        AuditFindingResponse: {
            /** Id */
            id: string;
            /** Category */
            category: string;
            /** Code */
            code: string;
            /** Severity */
            severity: string;
            /** Title */
            title: string;
            /** Evidence */
            evidence: {
                [key: string]: unknown;
            };
            /** Deterministic */
            deterministic: boolean;
        };
        /** AuditRunRequest */
        AuditRunRequest: {
            /** Target Role */
            target_role?: string | null;
            /** Content History */
            content_history?: string[] | null;
        };
        /** AuditRunResponse */
        AuditRunResponse: {
            /** Job Id */
            job_id: string;
            /**
             * Audit Status
             * @default queued
             * @constant
             */
            audit_status: "queued";
        };
        /** Body_create_upload_import_api_v1_profile_imports_upload_post */
        Body_create_upload_import_api_v1_profile_imports_upload_post: {
            /** File */
            file: string;
        };
        /** Body_parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post */
        Body_parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post: {
            /** File */
            file: string;
        };
        /** Body_submit_uploaded_samples_api_v1_content_voice_samples_upload_post */
        Body_submit_uploaded_samples_api_v1_content_voice_samples_upload_post: {
            /** File */
            file: string;
        };
        /** BulkScheduleRequest */
        BulkScheduleRequest: {
            cadence: components["schemas"]["Cadence"];
            /** Plan Ids */
            plan_ids: string[];
        };
        /** Cadence */
        Cadence: {
            /**
             * Days Of Week
             * @description 0=Monday ... 6=Sunday
             */
            days_of_week: number[];
            /** Time */
            time?: string | null;
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
            /** Weeks */
            weeks: number;
        };
        /** CarouselClosing */
        CarouselClosing: {
            /**
             * Cta
             * @default
             */
            cta: string;
        };
        /** CarouselCover */
        CarouselCover: {
            /** Headline */
            headline: string;
            /**
             * Subhead
             * @default
             */
            subhead: string;
        };
        /**
         * CarouselData
         * @description The carousel's re-editable structure -- stored as `Asset.body`
         *     (JSON) so the slide-by-slide editor can load it back exactly.
         */
        CarouselData: {
            /**
             * Template
             * @default clean
             * @enum {string}
             */
            template: "clean" | "bold" | "minimal";
            cover: components["schemas"]["CarouselCover"];
            /** Slides */
            slides: components["schemas"]["CarouselSlide"][];
            closing?: components["schemas"]["CarouselClosing"];
            /**
             * Caption
             * @default
             */
            caption: string;
        };
        /** CarouselResponse */
        CarouselResponse: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            data: components["schemas"]["CarouselData"];
        };
        /** CarouselSlide */
        CarouselSlide: {
            /** Headline */
            headline: string;
            /** Body */
            body: string;
            /**
             * Visual Note
             * @default
             */
            visual_note: string;
        };
        /** Certification */
        Certification: {
            /** Name */
            name?: string | null;
            /** Issuer */
            issuer?: string | null;
            issued?: components["schemas"]["DatePart"] | null;
            /** Credential Id */
            credential_id?: string | null;
            /** Url */
            url?: string | null;
        };
        /** ChangePasswordRequest */
        ChangePasswordRequest: {
            /** Current Password */
            current_password: string;
            /** New Password */
            new_password: string;
        };
        /** CommitImportRequest */
        CommitImportRequest: {
            payload: components["schemas"]["ProfileSnapshot"];
        };
        /** CommitResumeRequest */
        CommitResumeRequest: {
            /** Title */
            title: string;
            /** Source */
            source: string;
            document: components["schemas"]["ResumeDocument"];
            /** Original File Ref */
            original_file_ref?: string | null;
        };
        /** ConsistencyWeek */
        ConsistencyWeek: {
            /**
             * Week Start
             * Format: date
             */
            week_start: string;
            /** Posted Count */
            posted_count: number;
        };
        /** ContentPlanCreate */
        ContentPlanCreate: {
            /** Asset Id */
            asset_id?: string | null;
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Body Preview
             * @default
             */
            body_preview: string;
            /**
             * Content Type
             * @default post
             */
            content_type: string;
            /**
             * Status
             * @default idea
             * @enum {string}
             */
            status: "idea" | "drafted" | "ready" | "scheduled" | "posted" | "skipped";
            /**
             * Planned For
             * Format: date
             */
            planned_for: string;
            /** Planned Time */
            planned_time?: string | null;
            /** Tags */
            tags?: string[];
            /**
             * Notes
             * @default
             */
            notes: string;
        };
        /** ContentPlanResponse */
        ContentPlanResponse: {
            /** Id */
            id: string;
            /** Asset Id */
            asset_id: string | null;
            /** Title */
            title: string;
            /** Body Preview */
            body_preview: string;
            /** Content Type */
            content_type: string;
            /**
             * Status
             * @enum {string}
             */
            status: "idea" | "drafted" | "ready" | "scheduled" | "posted" | "skipped";
            /**
             * Planned For
             * Format: date
             */
            planned_for: string;
            /** Planned Time */
            planned_time: string | null;
            /** Posted At */
            posted_at: string | null;
            /** Reminder At */
            reminder_at: string | null;
            /** Recurrence Rule */
            recurrence_rule: string | null;
            /** Tags */
            tags: string[];
            /** Performance */
            performance: {
                [key: string]: number | string;
            };
            /** Notes */
            notes: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ContentPlanUpdate */
        ContentPlanUpdate: {
            /** Title */
            title?: string | null;
            /** Body Preview */
            body_preview?: string | null;
            /** Content Type */
            content_type?: string | null;
            /** Status */
            status?: ("idea" | "drafted" | "ready" | "scheduled" | "posted" | "skipped") | null;
            /** Tags */
            tags?: string[] | null;
            /** Notes */
            notes?: string | null;
        };
        /** CreateAssetRequest */
        CreateAssetRequest: {
            /** @default post */
            type: components["schemas"]["AssetType"];
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Folder Id */
            folder_id?: string | null;
        };
        /** CreateResumeMatchRequest */
        CreateResumeMatchRequest: {
            /** Resume Id */
            resume_id: string;
            /** Job Description Id */
            job_description_id: string;
        };
        /** DashboardHealthScore */
        DashboardHealthScore: {
            /** Audit Id */
            audit_id: string;
            /** Overall */
            overall: number | null;
            /** Scoring Version */
            scoring_version: string;
            /** Status */
            status: string;
            /** Completed At */
            completed_at: string | null;
            /** Categories */
            categories: components["schemas"]["AuditCategoryResultResponse"][];
        };
        /** DashboardResponse */
        DashboardResponse: {
            user: components["schemas"]["DashboardUser"];
            /** Is First Time */
            is_first_time: boolean;
            health_score: components["schemas"]["DashboardHealthScore"] | null;
            score_history: components["schemas"]["DashboardScoreHistory"];
            /** Top Recommendations */
            top_recommendations: components["schemas"]["RecommendationResponse"][];
            run_audit: components["schemas"]["DashboardRunAuditState"];
            /** Hubs */
            hubs: {
                [key: string]: boolean;
            };
        };
        /** DashboardRunAuditState */
        DashboardRunAuditState: {
            /** Can Run */
            can_run: boolean;
            /** Reason */
            reason: ("no_active_snapshot" | "audit_in_progress" | "cooldown_active" | "quota_exceeded") | null;
            /** Retry After Seconds */
            retry_after_seconds: number | null;
            /** In Flight Job Id */
            in_flight_job_id: string | null;
            /** Quota Used */
            quota_used: number;
            /** Quota Limit */
            quota_limit: number;
        };
        /** DashboardScoreHistory */
        DashboardScoreHistory: {
            /** Range */
            range: string;
            /** Points */
            points: components["schemas"]["ScoreHistoryPoint"][];
            /** Delta */
            delta: number | null;
        };
        /** DashboardUser */
        DashboardUser: {
            /** Full Name */
            full_name: string;
            /** Plan */
            plan: string;
        };
        /**
         * DatePart
         * @description A partial date as LinkedIn and resumes actually give it to us.
         */
        DatePart: {
            /** Year */
            year?: number | null;
            /** Month */
            month?: number | null;
        };
        /** DeleteAccountRequest */
        DeleteAccountRequest: {
            /** Current Password */
            current_password?: string | null;
        };
        /** Education */
        Education: {
            /** School */
            school?: string | null;
            /** Degree */
            degree?: string | null;
            /** Field */
            field?: string | null;
            /** Start Year */
            start_year?: number | null;
            /** End Year */
            end_year?: number | null;
            /** Description */
            description?: string | null;
        };
        /** Experience */
        Experience: {
            /** Company */
            company?: string | null;
            /** Title */
            title?: string | null;
            /** Employment Type */
            employment_type?: string | null;
            /** Location */
            location?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
            /** Is Current */
            is_current?: boolean | null;
            /** Description */
            description?: string | null;
            /** Bullets */
            bullets?: string[] | null;
            /** Skills */
            skills?: string[] | null;
        };
        /** FieldChange */
        FieldChange: {
            /** Path */
            path: string;
            /** Before */
            before: unknown | null;
            /** After */
            after: unknown | null;
        };
        /** FieldProvenance */
        FieldProvenance: {
            source: components["schemas"]["ProfileSource"];
            /** Confidence */
            confidence: number;
        };
        /** ForgotPasswordRequest */
        ForgotPasswordRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
        };
        /** GatewayMetricsResponse */
        GatewayMetricsResponse: {
            /** Window Hours */
            window_hours: number;
            /** Total Invocations */
            total_invocations: number;
            /** Latency P50 Ms */
            latency_p50_ms: number | null;
            /** Latency P95 Ms */
            latency_p95_ms: number | null;
            /** Cache Hit Rate */
            cache_hit_rate: number | null;
            /** Fallback Rate */
            fallback_rate: number | null;
            /** Invalid Output Rate */
            invalid_output_rate: number | null;
            /** Cost Per User Per Day Minor */
            cost_per_user_per_day_minor: {
                [key: string]: number;
            };
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /**
         * Hub
         * @enum {string}
         */
        Hub: "profile" | "content" | "engagement" | "career" | "growth";
        /** Identity */
        Identity: {
            /** Full Name */
            full_name?: string | null;
            /** Headline */
            headline?: string | null;
            /** Custom Url */
            custom_url?: string | null;
            /** Industry */
            industry?: string | null;
            /** Location */
            location?: string | null;
            /** Profile Picture Url */
            profile_picture_url?: string | null;
        };
        /** ImportPasteRequest */
        ImportPasteRequest: {
            /** Text */
            text: string;
        };
        /** ImportResponse */
        ImportResponse: {
            /** Import Id */
            import_id: string;
            /** Status */
            status: string;
            draft?: components["schemas"]["ProfileSnapshot"] | null;
            /**
             * Parse Warnings
             * @default []
             */
            parse_warnings: string[];
            /** Error */
            error?: string | null;
        };
        /** JobDescriptionParseRequest */
        JobDescriptionParseRequest: {
            /** Title */
            title: string;
            /** Company */
            company?: string | null;
            /** Raw Text */
            raw_text: string;
        };
        /** JobDescriptionResponse */
        JobDescriptionResponse: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            /** Company */
            company: string | null;
            /** Source */
            source: string;
            /** Raw Text */
            raw_text: string;
            /** Parsed */
            parsed: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** JobStatusResponse */
        JobStatusResponse: {
            /** Id */
            id: string;
            /** Type */
            type: string;
            /** Status */
            status: string;
            /** Attempts */
            attempts: number;
            /** Max Attempts */
            max_attempts: number;
            /** Progress Percent */
            progress_percent: number;
            /** Error */
            error: string | null;
            /** Result */
            result: {
                [key: string]: unknown;
            } | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Started At */
            started_at: string | null;
            /** Finished At */
            finished_at: string | null;
        };
        /** Language */
        Language: {
            /** Name */
            name?: string | null;
            /** Proficiency */
            proficiency?: string | null;
        };
        /** LinkedInStartResponse */
        LinkedInStartResponse: {
            /** Authorization Url */
            authorization_url: string;
        };
        /** ListItemChange */
        ListItemChange: {
            /** Key */
            key: string;
            /** Change */
            change: string;
            /** Before */
            before?: {
                [key: string]: unknown;
            } | null;
            /** After */
            after?: {
                [key: string]: unknown;
            } | null;
            /**
             * Field Changes
             * @default []
             */
            field_changes: components["schemas"]["FieldChange"][];
        };
        /** LoginRequest */
        LoginRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
        };
        /** LoginResponse */
        LoginResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            /** Expires In */
            expires_in: number;
            user: components["schemas"]["UserPublic"];
        };
        /** MarkContentPlanPostedRequest */
        MarkContentPlanPostedRequest: {
            /** Linkedin Url */
            linkedin_url?: string | null;
            /** Posted At */
            posted_at?: string | null;
            performance?: components["schemas"]["PerformanceNumbers"] | null;
        };
        /** MarkPostedRequest */
        MarkPostedRequest: {
            /** Linkedin Url */
            linkedin_url?: string | null;
        };
        /** MeResponse */
        MeResponse: {
            user: components["schemas"]["UserPublic"];
            /** Feature Flags */
            feature_flags: {
                [key: string]: boolean;
            };
        };
        /** MessageResponse */
        MessageResponse: {
            /** Message */
            message: string;
        };
        /** Metrics */
        Metrics: {
            /** Connections */
            connections?: number | null;
            /** Followers */
            followers?: number | null;
            /** Recommendations Received */
            recommendations_received?: number | null;
        };
        /** PerformanceNumbers */
        PerformanceNumbers: {
            /** Impressions */
            impressions?: number | null;
            /** Reactions */
            reactions?: number | null;
            /** Comments */
            comments?: number | null;
            /** Reposts */
            reposts?: number | null;
            /** Profile Views */
            profile_views?: number | null;
        };
        /** PerformanceSummaryResponse */
        PerformanceSummaryResponse: {
            /** Sufficient Data */
            sufficient_data: boolean;
            /** Total Data Points */
            total_data_points: number;
            /** By Content Type */
            by_content_type: components["schemas"]["PostTypePerformance"][];
        };
        /** PlaygroundPromptSummary */
        PlaygroundPromptSummary: {
            /** Id */
            id: string;
            /** Version */
            version: number;
            /** Tier */
            tier: string;
            /** Description */
            description: string;
            /** Required Context */
            required_context: string[];
            /** Output Schema */
            output_schema: {
                [key: string]: unknown;
            } | null;
            /** Max Output Tokens */
            max_output_tokens: number;
            /** Temperature */
            temperature: number;
            /** Cache Ttl Seconds */
            cache_ttl_seconds: number;
        };
        /** PlaygroundRunRequest */
        PlaygroundRunRequest: {
            /** Prompt Id */
            prompt_id: string;
            /** Context */
            context: {
                [key: string]: string;
            };
            /** Tier Override */
            tier_override?: string | null;
        };
        /** PlaygroundRunResponse */
        PlaygroundRunResponse: {
            /** Text */
            text: string | null;
            /** Parsed */
            parsed: unknown | null;
            /** Model */
            model: string;
            /** Provider */
            provider: string;
            /** Tokens In */
            tokens_in: number;
            /** Tokens Out */
            tokens_out: number;
            /** Cost Minor */
            cost_minor: number;
            /** Currency */
            currency: string;
            /** Latency Ms */
            latency_ms: number;
            /** Cached */
            cached: boolean;
            /** Fallback Used */
            fallback_used: boolean;
            /** Correlation Id */
            correlation_id: string;
        };
        /** PostTypePerformance */
        PostTypePerformance: {
            /** Content Type */
            content_type: string;
            /** Sample Size */
            sample_size: number;
            /** Median Engagement */
            median_engagement: number;
        };
        /**
         * ProfileSnapshot
         * @description The one canonical shape every input path must converge on.
         */
        ProfileSnapshot: {
            /**
             * Version
             * @default 1
             */
            version: number;
            source: components["schemas"]["ProfileSource"];
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            identity?: components["schemas"]["Identity"] | null;
            /** About */
            about?: string | null;
            /** Experiences */
            experiences?: components["schemas"]["Experience"][] | null;
            /** Education */
            education?: components["schemas"]["Education"][] | null;
            /** Skills */
            skills?: components["schemas"]["Skill"][] | null;
            /** Certifications */
            certifications?: components["schemas"]["Certification"][] | null;
            /** Languages */
            languages?: components["schemas"]["Language"][] | null;
            /** Projects */
            projects?: components["schemas"]["Project"][] | null;
            metrics?: components["schemas"]["Metrics"] | null;
            /** Field Provenance */
            field_provenance?: {
                [key: string]: components["schemas"]["FieldProvenance"];
            };
        };
        /**
         * ProfileSource
         * @enum {string}
         */
        ProfileSource: "linkedin_api" | "paste" | "upload_pdf" | "upload_docx" | "manual" | "merged";
        /** Project */
        Project: {
            /** Name */
            name?: string | null;
            /** Description */
            description?: string | null;
            /** Url */
            url?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
        };
        /**
         * ProvenanceSource
         * @description Where one field of a parsed ResumeDocument came from -- distinct
         *     from `ResumeSource` (which describes the whole document): a single
         *     upload can still have most fields parsed deterministically and a
         *     handful resolved by the one-shot AI pass for ambiguous segments.
         * @enum {string}
         */
        ProvenanceSource: "deterministic_parse" | "ai_resolved" | "user_edited" | "built" | "imported_from_profile";
        /** QuotaInfo */
        QuotaInfo: {
            /** Metric */
            metric: string;
            /** Used */
            used: number;
            /** Limit */
            limit: number;
        };
        /** RateRequest */
        RateRequest: {
            /**
             * Rating
             * @enum {string}
             */
            rating: "up" | "down";
            /** Feedback Text */
            feedback_text?: string | null;
        };
        /** RateResponse */
        RateResponse: {
            /** Run Id */
            run_id: string;
            /** Rating */
            rating: string;
            /** Feedback Text */
            feedback_text: string | null;
        };
        /** RecommendationListResponse */
        RecommendationListResponse: {
            /** Items */
            items: components["schemas"]["RecommendationResponse"][];
            /** Next Cursor */
            next_cursor: string | null;
        };
        /** RecommendationResponse */
        RecommendationResponse: {
            /** Id */
            id: string;
            /** Audit Id */
            audit_id: string;
            /** Category */
            category: string;
            /** Priority */
            priority: number;
            /** Title */
            title: string;
            /** Why */
            why: string;
            /** Action Label */
            action_label: string;
            /** Action Route */
            action_route: string;
            /** Action Tool Id */
            action_tool_id: string | null;
            /** Estimated Impact Points */
            estimated_impact_points: number;
            /** Status */
            status: string;
            /** Completed At */
            completed_at: string | null;
        };
        /** RecommendationUpdateRequest */
        RecommendationUpdateRequest: {
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "in_progress" | "done" | "dismissed";
        };
        /** RecurringSlotsRequest */
        RecurringSlotsRequest: {
            cadence: components["schemas"]["Cadence"];
        };
        /** RefreshResponse */
        RefreshResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            /** Expires In */
            expires_in: number;
        };
        /** RegenerateRequest */
        RegenerateRequest: {
            /** Nudge */
            nudge?: string | null;
        };
        /** RegisterRequest */
        RegisterRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
            /** Full Name */
            full_name: string;
        };
        /** ReminderRequest */
        ReminderRequest: {
            /** Reminder At */
            reminder_at?: string | null;
        };
        /** RescheduleRequest */
        RescheduleRequest: {
            /**
             * Planned For
             * Format: date
             */
            planned_for: string;
            /** Planned Time */
            planned_time?: string | null;
        };
        /** ResendVerificationRequest */
        ResendVerificationRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
        };
        /** ResetPasswordRequest */
        ResetPasswordRequest: {
            /** Token */
            token: string;
            /** New Password */
            new_password: string;
        };
        /** ResumeAward */
        ResumeAward: {
            /** Name */
            name?: string | null;
            /** Issuer */
            issuer?: string | null;
            date?: components["schemas"]["DatePart"] | null;
            /** Description */
            description?: string | null;
        };
        /** ResumeCertification */
        ResumeCertification: {
            /** Name */
            name?: string | null;
            /** Issuer */
            issuer?: string | null;
            issued?: components["schemas"]["DatePart"] | null;
            /** Credential Id */
            credential_id?: string | null;
            /** Url */
            url?: string | null;
        };
        /** ResumeContact */
        ResumeContact: {
            /** Full Name */
            full_name?: string | null;
            /** Email */
            email?: string | null;
            /** Phone */
            phone?: string | null;
            /** Location */
            location?: string | null;
            /** Linkedin Url */
            linkedin_url?: string | null;
            /** Website Url */
            website_url?: string | null;
        };
        /** ResumeCustomSection */
        ResumeCustomSection: {
            /** Heading */
            heading: string;
            /** Bullets */
            bullets?: string[];
        };
        /**
         * ResumeDocument
         * @description The one canonical shape every resume input path must converge on.
         */
        ResumeDocument: {
            /**
             * Version
             * @default 1
             */
            version: number;
            source: components["schemas"]["ResumeSource"];
            contact?: components["schemas"]["ResumeContact"] | null;
            /** Summary */
            summary?: string | null;
            /** Experiences */
            experiences?: components["schemas"]["ResumeExperience"][];
            /** Education */
            education?: components["schemas"]["ResumeEducation"][];
            skills?: components["schemas"]["ResumeSkills"] | null;
            /** Certifications */
            certifications?: components["schemas"]["ResumeCertification"][];
            /** Projects */
            projects?: components["schemas"]["ResumeProject"][];
            /** Awards */
            awards?: components["schemas"]["ResumeAward"][];
            /** Publications */
            publications?: components["schemas"]["ResumePublication"][];
            /** Custom Sections */
            custom_sections?: components["schemas"]["ResumeCustomSection"][];
            /** Field Provenance */
            field_provenance?: {
                [key: string]: components["schemas"]["ResumeFieldProvenance"];
            };
        };
        /** ResumeEducation */
        ResumeEducation: {
            /** School */
            school?: string | null;
            /** Degree */
            degree?: string | null;
            /** Field */
            field?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
            /** Description */
            description?: string | null;
        };
        /** ResumeExperience */
        ResumeExperience: {
            /** Company */
            company?: string | null;
            /** Title */
            title?: string | null;
            /** Location */
            location?: string | null;
            start?: components["schemas"]["DatePart"] | null;
            end?: components["schemas"]["DatePart"] | null;
            /** Is Current */
            is_current?: boolean | null;
            /** Bullets */
            bullets?: string[];
            /** Technologies */
            technologies?: string[];
        };
        /** ResumeFieldProvenance */
        ResumeFieldProvenance: {
            source: components["schemas"]["ProvenanceSource"];
            /** Confidence */
            confidence: number;
        };
        /** ResumeMatchResponse */
        ResumeMatchResponse: {
            /** Id */
            id: string;
            /** Resume Id */
            resume_id: string;
            /** Job Description Id */
            job_description_id: string;
            /** Overall Match */
            overall_match: number;
            /** Component Scores */
            component_scores: unknown[];
            /** Matched */
            matched: unknown[];
            /** Missing */
            missing: unknown[];
            /** Transferable */
            transferable: unknown[];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * ResumeParseResponse
         * @description Returned by the paste/upload parse endpoints -- always a draft
         *     for the user to review and correct, never yet committed.
         */
        ResumeParseResponse: {
            draft: components["schemas"]["ResumeDocument"];
            /** Warnings */
            warnings: string[];
        };
        /** ResumeProject */
        ResumeProject: {
            /** Name */
            name?: string | null;
            /** Description */
            description?: string | null;
            /** Url */
            url?: string | null;
            /** Technologies */
            technologies?: string[];
        };
        /** ResumePublication */
        ResumePublication: {
            /** Title */
            title?: string | null;
            /** Publisher */
            publisher?: string | null;
            date?: components["schemas"]["DatePart"] | null;
            /** Url */
            url?: string | null;
            /** Description */
            description?: string | null;
        };
        /** ResumeResponse */
        ResumeResponse: {
            /** Id */
            id: string;
            /** Title */
            title: string;
            /** Source */
            source: string;
            parsed: components["schemas"]["ResumeDocument"];
            /** Version */
            version: number;
            /** Is Active */
            is_active: boolean;
            /** Ats Score */
            ats_score: number | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ResumeSkills */
        ResumeSkills: {
            /** Technical */
            technical?: string[];
            /** Tools */
            tools?: string[];
            /** Soft */
            soft?: string[];
        };
        /**
         * ResumeSource
         * @enum {string}
         */
        ResumeSource: "upload" | "built" | "imported_from_profile";
        /** SaveAssetRequest */
        SaveAssetRequest: {
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Folder Id */
            folder_id?: string | null;
        };
        /** SaveCarouselRequest */
        SaveCarouselRequest: {
            /** Title */
            title: string;
            data: components["schemas"]["CarouselData"];
        };
        /** ScoreHistoryPoint */
        ScoreHistoryPoint: {
            /** Audit Id */
            audit_id: string;
            /**
             * Recorded At
             * Format: date-time
             */
            recorded_at: string;
            /** Overall */
            overall: number;
            /** Profile */
            profile: number | null;
            /** Content */
            content: number | null;
            /** Engagement */
            engagement: number | null;
            /** Career */
            career: number | null;
            /** Visibility */
            visibility: number | null;
        };
        /** ScoreHistoryResponse */
        ScoreHistoryResponse: {
            /** Range */
            range: string;
            /** Points */
            points: components["schemas"]["ScoreHistoryPoint"][];
        };
        /** SessionOut */
        SessionOut: {
            /** Id */
            id: string;
            /** User Agent */
            user_agent: string | null;
            /**
             * Issued At
             * Format: date-time
             */
            issued_at: string;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Current */
            current: boolean;
        };
        /** Skill */
        Skill: {
            /** Name */
            name?: string | null;
            /** Endorsements */
            endorsements?: number | null;
            /** Is Top */
            is_top?: boolean | null;
        };
        /** SnapshotDetail */
        SnapshotDetail: {
            /** Version */
            version: number;
            /** Source */
            source: string;
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            /** Completeness Score */
            completeness_score: number | null;
            /** Is Active */
            is_active: boolean;
            payload: components["schemas"]["ProfileSnapshot"];
        };
        /** SnapshotDiff */
        SnapshotDiff: {
            /** From Version */
            from_version: number;
            /** To Version */
            to_version: number;
            /** Field Changes */
            field_changes: components["schemas"]["FieldChange"][];
            /** List Changes */
            list_changes: {
                [key: string]: components["schemas"]["ListItemChange"][];
            };
        };
        /**
         * SnapshotSummary
         * @description One row of `GET /api/v1/profile/snapshots` — no payload, just enough
         *     to list and pick a version.
         */
        SnapshotSummary: {
            /** Version */
            version: number;
            /** Source */
            source: string;
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            /** Completeness Score */
            completeness_score: number | null;
            /** Is Active */
            is_active: boolean;
        };
        /** SyncResponse */
        SyncResponse: {
            draft: components["schemas"]["ProfileSnapshot"];
            /** Available Fields */
            available_fields: string[];
        };
        /** ToolRunRequest */
        ToolRunRequest: {
            /** Input */
            input: {
                [key: string]: unknown;
            };
        };
        /** ToolRunResponse */
        ToolRunResponse: {
            /** Run Id */
            run_id: string;
            /** Output */
            output: {
                [key: string]: unknown;
            };
            /** Context Used */
            context_used: string[];
            quota: components["schemas"]["QuotaInfo"];
            /** Warning */
            warning?: string | null;
        };
        /**
         * ToolRunSummary
         * @description One row of `GET /api/v1/tools/{id}/runs`.
         */
        ToolRunSummary: {
            /** Id */
            id: string;
            /** Input */
            input: {
                [key: string]: unknown;
            };
            /** Output */
            output: {
                [key: string]: unknown;
            } | null;
            /** Context Used */
            context_used: string[];
            /** Status */
            status: string;
            /** Rating */
            rating: string | null;
            /** Feedback Text */
            feedback_text: string | null;
            /** Parent Run Id */
            parent_run_id: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * ToolSummary
         * @description One row of `GET /api/v1/tools` -- everything the web app needs to
         *     render a tool card and, on selection, a fully working form and
         *     result view with no tool-specific frontend code.
         */
        ToolSummary: {
            /** Id */
            id: string;
            /** Hub */
            hub: string;
            /** Name */
            name: string;
            /** Short Description */
            short_description: string;
            /** Input Schema */
            input_schema: {
                [key: string]: unknown;
            };
            /** Output Schema */
            output_schema: {
                [key: string]: unknown;
            };
            /** Required Context */
            required_context: string[];
            /** Optional Context */
            optional_context: string[];
            /** Min Plan */
            min_plan: string;
            /** Quota Metric */
            quota_metric: string;
            /** Result Renderer */
            result_renderer: string;
            /** Save As */
            save_as: string | null;
            /** Free Daily Cap */
            free_daily_cap: number | null;
            /** Supports Streaming */
            supports_streaming: boolean;
            /** Counts As Outreach */
            counts_as_outreach: boolean;
        };
        /** UpdateProfileRequest */
        UpdateProfileRequest: {
            /** Full Name */
            full_name?: string | null;
            /** Locale */
            locale?: string | null;
            /** Timezone */
            timezone?: string | null;
        };
        /** UserPublic */
        UserPublic: {
            /** Id */
            id: string;
            /** Email */
            email: string;
            /** Full Name */
            full_name: string;
            /** Avatar Url */
            avatar_url: string | null;
            /** Locale */
            locale: string;
            /** Timezone */
            timezone: string;
            /** Role */
            role: string;
            /** Plan */
            plan: string;
            /** Email Verified */
            email_verified: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** VerifyEmailRequest */
        VerifyEmailRequest: {
            /** Token */
            token: string;
        };
        /** VoiceDescriptorResponse */
        VoiceDescriptorResponse: {
            /**
             * Source
             * @enum {string}
             */
            source: "supplied" | "derived" | "default";
            /** Sample Count */
            sample_count: number;
            /** Tone Adjectives */
            tone_adjectives: string[];
            /** Recurring Themes */
            recurring_themes: string[];
            /** Signature Structures */
            signature_structures: string[];
            /** Vocabulary Preferences */
            vocabulary_preferences: string[];
            /** Never Does */
            never_does: string[];
        };
        /** VoiceSamplesRequest */
        VoiceSamplesRequest: {
            /** Texts */
            texts: string[];
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    register_api_v1_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    verify_email_api_v1_auth_verify_email_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyEmailRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    resend_verification_api_v1_auth_resend_verification_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResendVerificationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_api_v1_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RefreshResponse"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
        };
    };
    logout_all_api_v1_auth_logout_all_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
        };
    };
    list_sessions_api_v1_auth_sessions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionOut"][];
                };
            };
        };
    };
    delete_session_api_v1_auth_sessions__session_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    forgot_password_api_v1_auth_forgot_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ForgotPasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reset_password_api_v1_auth_reset_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResetPasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    change_password_api_v1_auth_change_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangePasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    linkedin_start_api_v1_auth_linkedin_start_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LinkedInStartResponse"];
                };
            };
        };
    };
    linkedin_callback_api_v1_auth_linkedin_callback_get: {
        parameters: {
            query: {
                code: string;
                state: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_api_v1_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeResponse"];
                };
            };
        };
    };
    delete_me_api_v1_me_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DeleteAccountRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_me_api_v1_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UpdateProfileRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserPublic"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    connect_api_v1_profile_connect_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LinkedInStartResponse"];
                };
            };
        };
    };
    connect_callback_api_v1_profile_connect_callback_get: {
        parameters: {
            query: {
                code: string;
                state: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MessageResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sync_api_v1_profile_sync_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SyncResponse"];
                };
            };
        };
    };
    commit_sync_api_v1_profile_sync_commit_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommitImportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_paste_import_api_v1_profile_imports_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImportPasteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_upload_import_api_v1_profile_imports_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_create_upload_import_api_v1_profile_imports_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    commit_import_api_v1_profile_imports__import_id__commit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                import_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommitImportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_current_snapshot_api_v1_profile_snapshot_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotDetail"];
                };
            };
        };
    };
    put_manual_snapshot_api_v1_profile_snapshot_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProfileSnapshot"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_snapshots_api_v1_profile_snapshots_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotSummary"][];
                };
            };
        };
    };
    get_snapshot_diff_api_v1_profile_snapshots__version_a__diff__version_b__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                version_a: number;
                version_b: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotDiff"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_gateway_metrics_internal_metrics_get: {
        parameters: {
            query?: {
                window_hours?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GatewayMetricsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_playground_prompts_internal_playground_prompts_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaygroundPromptSummary"][];
                };
            };
        };
    };
    run_playground_prompt_internal_playground_run_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaygroundRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaygroundRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    stream_playground_prompt_internal_playground_stream_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaygroundRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_job_status_api_v1_jobs__job_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobStatusResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_audit_api_v1_audits_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AuditRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_latest_api_v1_audits_latest_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditDetailResponse"];
                };
            };
        };
    };
    get_audit_api_v1_audits__audit_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                audit_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_score_history_endpoint_api_v1_scores_history_get: {
        parameters: {
            query?: {
                range?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScoreHistoryResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_recommendations_api_v1_recommendations_get: {
        parameters: {
            query?: {
                status?: string | null;
                cursor?: number | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationListResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_recommendation_api_v1_recommendations__recommendation_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                recommendation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_dashboard_api_v1_dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DashboardResponse"];
                };
            };
        };
    };
    list_tools_api_v1_tools_get: {
        parameters: {
            query?: {
                hub?: components["schemas"]["Hub"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    run_tool_api_v1_tools__tool_id__run_post: {
        parameters: {
            query?: {
                stream?: boolean;
            };
            header?: never;
            path: {
                tool_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ToolRunRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_tool_runs_api_v1_tools__tool_id__runs_get: {
        parameters: {
            query?: {
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path: {
                tool_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolRunSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    regenerate_tool_run_api_v1_tools_runs__run_id__regenerate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegenerateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ToolRunResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    rate_tool_run_api_v1_tools_runs__run_id__rate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RateResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_tool_run_api_v1_tools_runs__run_id__save_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveAssetRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_voice_profile_api_v1_content_voice_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VoiceDescriptorResponse"];
                };
            };
        };
    };
    submit_pasted_samples_api_v1_content_voice_samples_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VoiceSamplesRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VoiceDescriptorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_uploaded_samples_api_v1_content_voice_samples_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_submit_uploaded_samples_api_v1_content_voice_samples_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VoiceDescriptorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_asset_endpoint_api_v1_assets_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateAssetRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_asset_posted_api_v1_assets__asset_id__mark_posted_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkPostedRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssetResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_carousel_endpoint_api_v1_carousels_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveCarouselRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CarouselResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_carousel_endpoint_api_v1_carousels__asset_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CarouselResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_carousel_endpoint_api_v1_carousels__asset_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SaveCarouselRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CarouselResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_carousel_pdf_endpoint_api_v1_carousels__asset_id__export_pdf_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_carousel_png_endpoint_api_v1_carousels__asset_id__export_png_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                asset_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_plans_endpoint_api_v1_content_plans_get: {
        parameters: {
            query: {
                start: string;
                end: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_plan_endpoint_api_v1_content_plans_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ContentPlanCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    consistency_endpoint_api_v1_content_plans_consistency_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConsistencyWeek"][];
                };
            };
        };
    };
    performance_summary_endpoint_api_v1_content_plans_performance_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PerformanceSummaryResponse"];
                };
            };
        };
    };
    get_plan_endpoint_api_v1_content_plans__plan_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_plan_endpoint_api_v1_content_plans__plan_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_plan_endpoint_api_v1_content_plans__plan_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ContentPlanUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reschedule_plan_endpoint_api_v1_content_plans__plan_id__reschedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RescheduleRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_reminder_endpoint_api_v1_content_plans__plan_id__reminder_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReminderRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_posted_endpoint_api_v1_content_plans__plan_id__mark_posted_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkContentPlanPostedRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_performance_endpoint_api_v1_content_plans__plan_id__performance_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PerformanceNumbers"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    recurring_slots_endpoint_api_v1_content_plans_recurring_slots_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecurringSlotsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    bulk_schedule_endpoint_api_v1_content_plans_bulk_schedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BulkScheduleRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ContentPlanResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    parse_resume_paste_endpoint_api_v1_career_resumes_parse_paste_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: string;
                };
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeParseResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_parse_resume_upload_endpoint_api_v1_career_resumes_parse_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeParseResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    parse_resume_from_profile_endpoint_api_v1_career_resumes_from_profile_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeParseResponse"];
                };
            };
        };
    };
    list_resumes_endpoint_api_v1_career_resumes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"][];
                };
            };
        };
    };
    commit_resume_endpoint_api_v1_career_resumes_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CommitResumeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_resume_endpoint_api_v1_career_resumes__resume_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_resume_endpoint_api_v1_career_resumes__resume_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_resume_endpoint_api_v1_career_resumes__resume_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_resume_pdf_endpoint_api_v1_career_resumes__resume_id__export_pdf_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_resume_docx_endpoint_api_v1_career_resumes__resume_id__export_docx_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                resume_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_job_descriptions_endpoint_api_v1_career_job_descriptions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobDescriptionResponse"][];
                };
            };
        };
    };
    create_job_description_endpoint_api_v1_career_job_descriptions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JobDescriptionParseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobDescriptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_description_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobDescriptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_job_description_endpoint_api_v1_career_job_descriptions__job_description_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_description_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_matches_endpoint_api_v1_career_matches_get: {
        parameters: {
            query?: {
                resume_id?: string | null;
                job_description_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeMatchResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_match_endpoint_api_v1_career_matches_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateResumeMatchRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResumeMatchResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
}
