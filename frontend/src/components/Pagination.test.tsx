import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Pagination from './Pagination'

describe('Pagination', () => {
  it('total <= 1 时不渲染任何内容', () => {
    const { container } = render(<Pagination current={1} total={1} onChange={vi.fn()} />)
    expect(container.firstChild).toBeNull()
  })

  it('渲染正确的页码按钮', () => {
    render(<Pagination current={1} total={5} onChange={vi.fn()} />)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('点击页码触发 onChange', () => {
    const handleChange = vi.fn()
    render(<Pagination current={1} total={5} onChange={handleChange} />)

    fireEvent.click(screen.getByText('3'))
    expect(handleChange).toHaveBeenCalledWith(3)
  })

  it('当前为第一页时，上一页按钮禁用', () => {
    render(<Pagination current={1} total={5} onChange={vi.fn()} />)

    const prevButton = screen.getAllByRole('button')[0]
    expect(prevButton).toBeDisabled()
  })

  it('当前为最后一页时，下一页按钮禁用', () => {
    render(<Pagination current={5} total={5} onChange={vi.fn()} />)

    const buttons = screen.getAllByRole('button')
    const nextButton = buttons[buttons.length - 1]
    expect(nextButton).toBeDisabled()
  })
})
