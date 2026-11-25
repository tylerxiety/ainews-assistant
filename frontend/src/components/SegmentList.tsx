import React from 'react'
import { TopicGroup, Segment } from '../types'
import { useLanguage } from '../i18n'
import { Pin, Check, Loader2 } from 'lucide-react'
import './SegmentList.css'

interface SegmentListProps {
    groups: TopicGroup[]
    currentGroupIndex: number
    currentSegmentIndex: number
    bookmarkedSegments: Set<string>
    bookmarkingSegment: string | null
    onSegmentClick: (groupIndex: number, segmentIndex: number) => void
    onBookmark: (e: React.MouseEvent, segment: Segment) => void
    language: string
}

export default function SegmentList({
    groups,
    currentGroupIndex,
    currentSegmentIndex,
    bookmarkedSegments,
    bookmarkingSegment,
    onSegmentClick,
    onBookmark,
    language
}: SegmentListProps) {
    const { t } = useLanguage()

    // Helper to render content with inline links
    const renderContentWithLinks = (content: string, links: Segment['links']) => {
        if (!links || links.length === 0) return <p>{content}</p>

        // Sort links by length descending to avoid partial matches
        const sortedLinks = [...links].sort((a, b) => (b.text?.length || 0) - (a.text?.length || 0))

        // We will construct an array of nodes
        let nodes: React.ReactNode[] = [content]
        let linkIndex = 0

        sortedLinks.forEach(link => {
            if (!link.text) return

            const newNodes: React.ReactNode[] = []
            nodes.forEach(node => {
                if (typeof node === 'string' && link.text) {
                    const parts = node.split(link.text)
                    parts.forEach((part, i) => {
                        newNodes.push(part)
                        if (i < parts.length - 1) {
                            newNodes.push(
                                <a
                                    key={`link-${linkIndex++}`}
                                    href={link.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="inline-link"
                                >
                                    {link.text}
                                </a>
                            )
                        }
                    })
                } else {
                    newNodes.push(node)
                }
            })
            nodes = newNodes
        })

        return <p>{nodes}</p>
    }

    return (
        <div className="segments-list">
            {groups.length === 0 ? (
                <p className="no-segments">{t('segmentList.noSegments')}</p>
            ) : (
                groups.map((group, groupIndex) => {
                    const groupLabel = language === 'zh' && group.label_zh
                        ? group.label_zh
                        : group.label

                    return (
                    <div
                        key={group.id}
                        id={`group-${group.id}`}
                        className={`${group.is_section_header ? 'section-header' : 'topic-group'} ${groupIndex === currentGroupIndex ? 'group-active' : ''}`}
                    >
                        <div className="group-content">
                            {groupLabel && (group.is_section_header ? (
                                <h2 className="section-title" onClick={() => onSegmentClick(groupIndex, 0)}>
                                    {groupLabel}
                                </h2>
                            ) : <h3 className="group-title">{groupLabel}</h3>)}

                            <div className="group-items">
                                {group.segments.map((segment, segmentIndex) => {
                                    const isActive = groupIndex === currentGroupIndex && segmentIndex === currentSegmentIndex
                                    const displayContent = language === 'zh' && segment.content_raw_zh
                                        ? segment.content_raw_zh
                                        : segment.content_raw
                                    return (
                                        <div
                                            key={segment.id}
                                            id={`segment-${segment.id}`}
                                            className={`segment group-item ${isActive ? 'active' : ''}`}
                                            onClick={() => onSegmentClick(groupIndex, segmentIndex)}
                                        >
                                            <div className="segment-content">
                                                {renderContentWithLinks(displayContent, segment.links)}
                                            </div>

                                            {/* Only show distinct bookmark button if active or bookmarked */}
                                            {(isActive || bookmarkedSegments.has(segment.id)) && (
                                                <button
                                                    className={`bookmark-btn ${bookmarkedSegments.has(segment.id) ? 'bookmarked' : ''}`}
                                                    onClick={(e) => onBookmark(e, segment)}
                                                    disabled={bookmarkingSegment === segment.id || bookmarkedSegments.has(segment.id)}
                                                    title={bookmarkedSegments.has(segment.id) ? t('segmentList.bookmarked') : t('segmentList.bookmarkToClickUp')}
                                                >
                                                    {bookmarkingSegment === segment.id ? (
                                                        <Loader2 className="animate-spin" size={18} />
                                                    ) : bookmarkedSegments.has(segment.id) ? (
                                                        <Check size={18} />
                                                    ) : (
                                                        <Pin size={18} />
                                                    )}
                                                </button>
                                            )}
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    </div>
                    )
                })
            )}
        </div>
    )
}
