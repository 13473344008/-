package dto

type SubmitReview struct {
	ExpectedEditVersion int64 `json:"expected_edit_version"`
}
type DecideReview struct {
	ReviewID        string `json:"review_id"`
	CandidateHash   string `json:"candidate_hash"`
	Comment         string `json:"comment"`
	RejectionReason string `json:"rejection_reason"`
}
type ReturnReview struct {
	ReviewID string `json:"review_id"`
	Reason   string `json:"reason"`
}
type ReviewQuery struct {
	PageIndex int    `form:"pageIndex"`
	PageSize  int    `form:"pageSize"`
	Search    string `form:"search"`
	State     string `form:"state"`
}
