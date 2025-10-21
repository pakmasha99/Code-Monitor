# Scoring System Update - Test Plan

## Summary of Changes

### Problem Identified
- **Lines Added**: Updates in real-time (2,500) ✅
- **Total Score**: Was 1101.1 (complex formula with quality/consistency metrics) ❌
- **Issue**: Score didn't update in real-time, complex formula was confusing

### Solution Implemented
- **New Formula**: `Score = code_lines_added + (documents_created × 100)`
- **Unit Changed**: "Points" → "Lines"
- **Real-Time Updates**: Triggers on both create and update submissions
- **Simplified Breakdown**: 100% Productivity (removed Quality/Consistency)

## Files Modified

### Backend Changes
1. **`backend/app/services/ranking_service.py`**
   - Simplified `calculate_weekly_score()` method
   - Removed complex weights system
   - New formula: Lines only (code + docs×100)
   - LINES_PER_DOCUMENT = 100

2. **`backend/app/api/weekly_submissions.py`**
   - Added ranking update trigger to `update_submission()` (PATCH endpoint)
   - Already had trigger in `create_weekly_submission()` (POST endpoint)

### Frontend Changes
3. **`frontend/src/app/dashboard/page.tsx`**
   - Changed "Points" → "Lines" in Total Score card
   - Changed "points" → "lines" in leaderboard table
   - Added `.toLocaleString()` for number formatting (e.g., "2,500")
   - Updated ScoreBreakdownChart to show 100% productivity
   - Extract productivity from API response

## Test Cases

### Test 1: Score Calculation Formula
**Given**:
- Code lines added: 2,500
- Documents created: 10

**Expected**:
- Score = 2,500 + (10 × 100) = **3,500 lines**

**Verify**:
```bash
# Check via API
curl http://localhost:8000/api/rankings/current | jq '.[] | {user: .user_name, score: .total_score}'

# Expected output for test user:
# {
#   "user": "Jiook Cha",
#   "score": 3500
# }
```

### Test 2: Real-Time Update (Create)
**Steps**:
1. Create new submission via POST
   ```bash
   curl -X POST http://localhost:8000/api/users/1/submissions \
     -H "Content-Type: application/json" \
     -d '{
       "week_start_date": "2025-10-20",
       "code_lines_added": 1500,
       "documents_created": 5
     }'
   ```
2. Immediately check ranking
   ```bash
   curl http://localhost:8000/api/rankings/current
   ```

**Expected**:
- Ranking is updated immediately (no delay)
- Score = 1,500 + (5 × 100) = **2,000 lines**

### Test 3: Real-Time Update (Update)
**Steps**:
1. Update existing submission via PATCH
   ```bash
   curl -X PATCH http://localhost:8000/api/users/1/submissions/1 \
     -H "Content-Type: application/json" \
     -d '{
       "code_lines_added": 3000,
       "documents_created": 15
     }'
   ```
2. Immediately check ranking

**Expected**:
- Ranking updates immediately after PATCH
- Score = 3,000 + (15 × 100) = **4,500 lines**

### Test 4: Frontend Display
**Steps**:
1. Navigate to dashboard after making submission
2. Refresh page

**Expected**:
- "Total Score" shows correct line count with formatting (e.g., "3,500")
- Label says "Lines" not "Points"
- Leaderboard shows "lines" not "points"
- Score Breakdown Chart shows 100% Productivity

### Test 5: Zero Submissions Edge Case
**Given**: User with no submissions

**Expected**:
- Score = 0 lines
- Productivity = 0
- No errors in calculation

### Test 6: Only Code, No Docs
**Given**:
- Code lines added: 5,000
- Documents created: 0

**Expected**:
- Score = 5,000 + (0 × 100) = **5,000 lines**

### Test 7: Only Docs, No Code
**Given**:
- Code lines added: 0
- Documents created: 20

**Expected**:
- Score = 0 + (20 × 100) = **2,000 lines**

### Test 8: Leaderboard Ranking Order
**Given**: Multiple users with different scores

**Expected**:
- Users ranked correctly by total lines (descending)
- Ties handled properly
- Top 3 shown with medals (🥇🥈🥉)

## Verification Checklist

- [ ] Backend starts without errors after changes
- [ ] POST /api/users/{user_id}/submissions triggers ranking update
- [ ] PATCH /api/users/{user_id}/submissions/{id} triggers ranking update
- [ ] GET /api/rankings/current returns scores in lines
- [ ] Frontend dashboard shows "Lines" not "Points"
- [ ] Leaderboard table shows "lines" not "points"
- [ ] Score breakdown shows 100% productivity
- [ ] Numbers are formatted with commas (e.g., "2,500")
- [ ] Real-time: Dashboard updates immediately after submission
- [ ] Formula: Score = code_lines + (docs × 100)

## Rollback Plan

If issues occur, revert these commits:
1. Revert ranking_service.py to complex scoring formula
2. Revert weekly_submissions.py PATCH endpoint change
3. Revert dashboard.tsx label changes

## Performance Considerations

**Before**: Rankings updated via scheduled task (could be delayed)

**After**: Rankings updated synchronously on submission
- Pros: Real-time feedback, no user confusion
- Cons: Slight performance impact (recalculates all week rankings)
- Mitigation: Only recalculates affected week, not all historical data

**Estimated Impact**:
- For 10 users: <50ms additional latency
- For 100 users: <200ms additional latency
- Acceptable for submission operation (user expects some processing time)

## Migration Notes

### Existing Data
All existing rankings will show different scores with new formula:
- Old: Complex weighted scores (0-1000+ range)
- New: Simple line counts (could be 0-10,000+ range)

### Recommended Actions
1. Run migration script to recalculate all historical rankings:
   ```bash
   python backend/scripts/recalculate_all_rankings.py
   ```
2. Or: Accept that historical data uses old formula (document this clearly)
3. Or: Clear all rankings and start fresh (lose historical comparison)

**Recommendation**: Option 1 (recalculate) for consistency

## Success Criteria

✅ Score updates immediately when submission is made
✅ Formula is simple and transparent (lines only)
✅ UI clearly shows "Lines" as the unit
✅ Leaderboard ranks users correctly by line count
✅ No errors in backend or frontend
✅ Performance is acceptable (<500ms for submission)

## Next Steps

1. Restart backend server to load new code
2. Test with actual submission on frontend
3. Verify dashboard shows updated score immediately
4. Monitor for any errors in logs
5. Collect user feedback on new simple scoring system
