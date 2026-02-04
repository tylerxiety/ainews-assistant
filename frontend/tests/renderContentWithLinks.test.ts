/**
 * Unit tests for the renderContentWithLinks algorithm extracted from SegmentList.tsx.
 *
 * The algorithm works by iterating over links (sorted by text length descending)
 * and progressively splitting string nodes on each link's text, inserting link
 * markers between the parts. Non-string nodes (already-linked) are passed through
 * unchanged.
 *
 * Bug under investigation: link text "StepFun" duplicates, producing
 * "StepFunStepFunStepFun Step-3.5-Flash..." instead of "StepFun Step-3.5-Flash..."
 */

import { describe, it, expect } from 'vitest'

// --- Types matching SegmentList usage ---
interface SegmentLink {
    text?: string
    url: string
}

// A rendered node is either a plain string or a link object.
interface LinkNode {
    type: 'link'
    text: string
    url: string
    key: string
}
type OutputNode = string | LinkNode

// --- BUGGY algorithm (original from SegmentList.tsx, pre-fix) ---
// Uses per-split index `i` for the key, which resets for each string fragment.
// When the same link text appears in multiple string fragments, keys collide.
function renderContentWithLinks_BUGGY(content: string, links: SegmentLink[] | undefined): OutputNode[] {
    if (!links || links.length === 0) return [content]

    const sortedLinks = [...links].sort((a, b) => (b.text?.length || 0) - (a.text?.length || 0))
    let nodes: OutputNode[] = [content]

    sortedLinks.forEach(link => {
        if (!link.text) return
        const newNodes: OutputNode[] = []
        nodes.forEach(node => {
            if (typeof node === 'string' && link.text) {
                const parts = node.split(link.text)
                parts.forEach((part, i) => {
                    newNodes.push(part)
                    if (i < parts.length - 1) {
                        // BUG: key uses `i` which resets per string fragment
                        newNodes.push({ type: 'link', text: link.text!, url: link.url, key: `${link.text}-${link.url}-${i}` })
                    }
                })
            } else {
                newNodes.push(node)
            }
        })
        nodes = newNodes
    })

    return nodes
}

// --- FIXED algorithm: uses a global linkIndex counter for unique keys ---
function renderContentWithLinks_FIXED(content: string, links: SegmentLink[] | undefined): OutputNode[] {
    if (!links || links.length === 0) return [content]

    const sortedLinks = [...links].sort((a, b) => (b.text?.length || 0) - (a.text?.length || 0))
    let nodes: OutputNode[] = [content]
    let linkIndex = 0

    sortedLinks.forEach(link => {
        if (!link.text) return
        const newNodes: OutputNode[] = []
        nodes.forEach(node => {
            if (typeof node === 'string' && link.text) {
                const parts = node.split(link.text)
                parts.forEach((part, i) => {
                    newNodes.push(part)
                    if (i < parts.length - 1) {
                        newNodes.push({ type: 'link', text: link.text!, url: link.url, key: `link-${linkIndex++}` })
                    }
                })
            } else {
                newNodes.push(node)
            }
        })
        nodes = newNodes
    })

    return nodes
}

// --- Helper: simulate textContent (what the browser would produce for the <p>) ---
function toTextContent(nodes: OutputNode[]): string {
    return nodes.map(n => (typeof n === 'string' ? n : n.text)).join('')
}

// --- Helper: count non-overlapping occurrences of a substring ---
function countOccurrences(str: string, sub: string): number {
    return (str.match(new RegExp(sub.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length
}

// --- Helper: count link nodes with a given text ---
function countLinkNodes(nodes: OutputNode[], text: string): number {
    return nodes.filter(n => typeof n !== 'string' && n.text === text).length
}

// --- Helper: extract React keys from link nodes ---
function extractKeys(nodes: OutputNode[]): string[] {
    return nodes.filter((n): n is LinkNode => typeof n !== 'string').map(n => n.key)
}

// --- Helper: check that all keys are unique ---
function hasUniqueKeys(nodes: OutputNode[]): boolean {
    const keys = extractKeys(nodes)
    return new Set(keys).size === keys.length
}

// ===========================================================================
// Exact reproduction data from the bug report
// ===========================================================================
const BUG_CONTENT =
    'StepFun Step-3.5-Flash open release (big efficiency claims): ' +
    "StepFun's Step-3.5-Flash is repeatedly cited as asparse MoEmodel with196B total parameters / ~11B active, " +
    'tuned forspeed + long-context agent workflows(notably256K contextwith3:1 sliding-window attention + full attention, ' +
    'plusMTP-3 multi-token prediction) (official release thread,launch/links). ' +
    'StepFun reports74.4% SWE-bench Verifiedand51.0% Terminal-Bench 2.0(StepFun).'

const BUG_LINKS: SegmentLink[] = [
    { text: 'official release thread', url: 'https://twitter.com/StepFun_ai/status/2018370831538180167' },
    { text: 'launch/links', url: 'https://twitter.com/CyouSakura/status/2018146246020772062' },
    { text: 'StepFun', url: 'https://twitter.com/StepFun_ai/status/2018370831538180167' },
]

describe('renderContentWithLinks -- bug reproduction (StepFun duplication)', () => {
    it('raw content has exactly 4 occurrences of "StepFun"', () => {
        // Baseline: confirm the test data is correct before running the algorithm
        expect(countOccurrences(BUG_CONTENT, 'StepFun')).toBe(4)
    })

    // --- Demonstrate the bug in the ORIGINAL (pre-fix) algorithm ---
    it('[BUGGY] original algorithm produces duplicate React keys', () => {
        const nodes = renderContentWithLinks_BUGGY(BUG_CONTENT, BUG_LINKS)

        // The data itself is correct (4 StepFun in textContent), but keys collide.
        expect(countOccurrences(toTextContent(nodes), 'StepFun')).toBe(4)

        // Keys are NOT unique -- this is what causes React to mis-render
        expect(hasUniqueKeys(nodes)).toBe(false)

        // Specifically: StepFun appears in two separate string fragments (split by
        // "official release thread" and "launch/links" links processed first).
        // Each fragment's split resets `i`, so keys like "StepFun-URL-0" appear twice.
        const keys = extractKeys(nodes)
        const keyCounts = new Map<string, number>()
        keys.forEach(k => keyCounts.set(k, (keyCounts.get(k) || 0) + 1))
        const duplicates = [...keyCounts.entries()].filter(([, count]) => count > 1)
        expect(duplicates.length).toBeGreaterThan(0)
    })

    // --- Verify the FIXED algorithm ---
    it('[FIXED] all React keys are unique', () => {
        const nodes = renderContentWithLinks_FIXED(BUG_CONTENT, BUG_LINKS)
        expect(hasUniqueKeys(nodes)).toBe(true)
    })

    it('[FIXED] rendered textContent has exactly 4 occurrences of "StepFun" (no duplication)', () => {
        const nodes = renderContentWithLinks_FIXED(BUG_CONTENT, BUG_LINKS)
        const text = toTextContent(nodes)
        expect(countOccurrences(text, 'StepFun')).toBe(4)
    })

    it('[FIXED] does not produce consecutive "StepFun" at the start of output', () => {
        const nodes = renderContentWithLinks_FIXED(BUG_CONTENT, BUG_LINKS)
        const text = toTextContent(nodes)

        expect(text.startsWith('StepFun ')).toBe(true)
        expect(text.startsWith('StepFunStepFun')).toBe(false)
    })

    it('[FIXED] each "StepFun" occurrence becomes exactly one link node', () => {
        const nodes = renderContentWithLinks_FIXED(BUG_CONTENT, BUG_LINKS)

        expect(countLinkNodes(nodes, 'StepFun')).toBe(4)

        // No bare "StepFun" in string fragments
        const stringNodes = nodes.filter(n => typeof n === 'string') as string[]
        const bareCount = stringNodes.reduce((sum, s) => sum + countOccurrences(s, 'StepFun'), 0)
        expect(bareCount).toBe(0)
    })

    it('[FIXED] other link texts are also correctly linked with unique keys', () => {
        const nodes = renderContentWithLinks_FIXED(BUG_CONTENT, BUG_LINKS)

        expect(countLinkNodes(nodes, 'official release thread')).toBe(1)
        expect(countLinkNodes(nodes, 'launch/links')).toBe(1)

        const stringNodes = nodes.filter(n => typeof n === 'string') as string[]
        expect(stringNodes.some(s => s.includes('official release thread'))).toBe(false)
        expect(stringNodes.some(s => s.includes('launch/links'))).toBe(false)

        expect(hasUniqueKeys(nodes)).toBe(true)
    })

    it('[FIXED] surrounding non-link text is fully preserved', () => {
        const nodes = renderContentWithLinks_FIXED(BUG_CONTENT, BUG_LINKS)
        const text = toTextContent(nodes)

        expect(text).toBe(BUG_CONTENT)
    })
})

// ===========================================================================
// Edge cases that could trigger duplication in general
// ===========================================================================
describe('renderContentWithLinks -- edge cases (all using FIXED algorithm)', () => {
    it('link text that is a substring of another link text does not cause duplication', () => {
        // "Fun" is a substring of "StepFun"; sorted by length, "StepFun" is processed first
        const content = 'StepFun is Fun and more Fun'
        const links: SegmentLink[] = [
            { text: 'StepFun', url: 'https://example.com/a' },
            { text: 'Fun', url: 'https://example.com/b' },
        ]
        const nodes = renderContentWithLinks_FIXED(content, links)
        const text = toTextContent(nodes)

        expect(text).toBe(content)
        expect(countLinkNodes(nodes, 'StepFun')).toBe(1)
        expect(countLinkNodes(nodes, 'Fun')).toBe(2)
        expect(hasUniqueKeys(nodes)).toBe(true)

        const strings = nodes.filter(n => typeof n === 'string') as string[]
        expect(strings.some(s => s.includes('Fun'))).toBe(false)
    })

    it('duplicate links in the array do not cause duplication or key collision', () => {
        const content = 'Hello World Hello'
        const links: SegmentLink[] = [
            { text: 'Hello', url: 'https://example.com/hello' },
            { text: 'Hello', url: 'https://example.com/hello' }, // duplicate
        ]
        const nodes = renderContentWithLinks_FIXED(content, links)
        const text = toTextContent(nodes)

        expect(text).toBe(content)
        expect(countOccurrences(text, 'Hello')).toBe(2)
        expect(hasUniqueKeys(nodes)).toBe(true)
    })

    it('link text at the very start of content is handled correctly', () => {
        const content = 'Apple is great. Apple pie.'
        const links: SegmentLink[] = [{ text: 'Apple', url: 'https://example.com' }]
        const nodes = renderContentWithLinks_FIXED(content, links)
        const text = toTextContent(nodes)

        expect(text).toBe(content)
        expect(countLinkNodes(nodes, 'Apple')).toBe(2)
        expect(text.startsWith('Apple')).toBe(true)
        expect(text.startsWith('AppleApple')).toBe(false)
        expect(hasUniqueKeys(nodes)).toBe(true)
    })

    it('link text at the very end of content is handled correctly', () => {
        const content = 'See the docs (link)'
        const links: SegmentLink[] = [{ text: 'link', url: 'https://example.com' }]
        const nodes = renderContentWithLinks_FIXED(content, links)
        const text = toTextContent(nodes)

        expect(text).toBe(content)
        expect(countLinkNodes(nodes, 'link')).toBe(1)
        expect(hasUniqueKeys(nodes)).toBe(true)
    })

    it('link with empty text is skipped', () => {
        const content = 'Hello World'
        const links: SegmentLink[] = [{ text: '', url: 'https://example.com' }]
        const nodes = renderContentWithLinks_FIXED(content, links)

        expect(toTextContent(nodes)).toBe(content)
    })

    it('link with undefined text is skipped', () => {
        const content = 'Hello World'
        const links: SegmentLink[] = [{ url: 'https://example.com' }] // text is undefined
        const nodes = renderContentWithLinks_FIXED(content, links)

        expect(toTextContent(nodes)).toBe(content)
    })

    it('no links returns content as single string node', () => {
        const content = 'No links here'
        const nodes = renderContentWithLinks_FIXED(content, [])
        expect(nodes).toEqual([content])
    })

    it('undefined links returns content as single string node', () => {
        const content = 'No links here'
        const nodes = renderContentWithLinks_FIXED(content, undefined)
        expect(nodes).toEqual([content])
    })

    it('link text that does not appear in content produces no link nodes', () => {
        const content = 'Hello World'
        const links: SegmentLink[] = [{ text: 'Goodbye', url: 'https://example.com' }]
        const nodes = renderContentWithLinks_FIXED(content, links)

        expect(countLinkNodes(nodes, 'Goodbye')).toBe(0)
        expect(toTextContent(nodes)).toBe(content)
    })

    it('two links sharing the same URL do not interfere with each other', () => {
        // Mirrors the bug data: "official release thread" and "StepFun" share a URL
        const content = 'See official release thread for StepFun details'
        const links: SegmentLink[] = [
            { text: 'official release thread', url: 'https://twitter.com/same' },
            { text: 'StepFun', url: 'https://twitter.com/same' },
        ]
        const nodes = renderContentWithLinks_FIXED(content, links)
        const text = toTextContent(nodes)

        expect(text).toBe(content)
        expect(countLinkNodes(nodes, 'official release thread')).toBe(1)
        expect(countLinkNodes(nodes, 'StepFun')).toBe(1)
        expect(hasUniqueKeys(nodes)).toBe(true)
    })

    it('many occurrences of the same link text all get unique keys', () => {
        const content = 'X and X and X and X and X'
        const links: SegmentLink[] = [{ text: 'X', url: 'https://example.com/x' }]
        const nodes = renderContentWithLinks_FIXED(content, links)

        expect(countLinkNodes(nodes, 'X')).toBe(5)
        expect(hasUniqueKeys(nodes)).toBe(true)
        expect(toTextContent(nodes)).toBe(content)
    })
})
